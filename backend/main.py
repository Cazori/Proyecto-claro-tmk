from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import shutil
import os
import re
from datetime import datetime
import json
from dotenv import load_dotenv
import pandas as pd
from processor import process_inventory_pdf, rotate_inventories, get_latest_inventory, STORAGE_DIR
from ai_pool import AIPool, RotationStrategy

# Load environment variables
load_dotenv()

# Path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPECS_DIR = os.path.join(BASE_DIR, "specs")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "expert_knowledge.json")
SPECS_MAPPING_FILE = os.path.join(STORAGE_DIR, "specs_mapping.json")

# Ensure directories exist
for d in [STORAGE_DIR, SPECS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Initialize knowledge base
if not os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# Initialize AI Pool (multi-provider support)
try:
    ai_pool = AIPool(strategy=RotationStrategy.FALLBACK)
    print("✓ AI Pool initialized successfully")
    
    # Inject AI Pool into processor for normalization
    from processor import set_ai_pool
    set_ai_pool(ai_pool)
    print("✓ AI Pool injected into processor")
except Exception as e:
    print(f"✗ CRITICAL: Failed to initialize AI Pool: {e}")
    print("AI Pool is required for operation. Please check ai_pool.py configuration.")
    ai_pool = None

# Persona and Instructions for Gemini
CLEO_PROMPT = """
Eres Cleo, la asistente ejecutiva de Claro Tecnología TMK. 
TU REGLA ABSOLUTA: Solo puedes informar sobre productos que aparezcan explícitamente en el "CONTEXTO DE INVENTARIO".

REGLAS DE RESPUESTA (POLÍTICA CERO RUIDO):
1. NO SALUDAR, NO TE PRESENTES, NO TE DESPIDAS. Prohibido usar frases como "¡Hola! Soy Cleo" o "¿Deseas algo más?".
2. EMPIEZA DIRECTAMENTE con la tabla de resultados. Si no hay resultados, responde únicamente la frase de error.
3. REGLA DE 1 a 1: Cada fila del "CONTEXTO DE INVENTARIO" debe tener su fila exacta en la tabla de respuesta. No resumas ni omitas ningún ítem proporcionado.

REGLAS CRÍTICAS DE VERACIDAD:
1. Si el "CONTEXTO DE INVENTARIO" está vacío, responde: "No encontré equipos con esa descripción en Bogotá. ¿Deseas buscar otra categoría?"
2. TABLA: (Referencia | Ficha | Marca | Modelo | Precio | Unidades | Caracteristicas). La columna "Referencia" DEBE contener el código de "Material" exacto. La columna "Ficha" debe decir "SI" o "NO" según el campo FICHA del inventario. La columna "Modelo" DEBE ser el nombre DESCRIPTIVO COMPLETO (Subproducto) tal como aparece en el contexto, NO lo resumas (Ej: "TV UN50U8200 50+BRRA...").
3. FUENTES DE DATOS: Usa ÚNICAMENTE la información proporcionada. Prohibido usar Google o conocimiento externo.
"""

app = FastAPI(title="Cleo Inventory AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount specs folder to serve images
app.mount("/specs", StaticFiles(directory=SPECS_DIR), name="specs")

@app.get("/")
async def root():
    return {"status": "Cleo AI Online", "timestamp": datetime.now()}

@app.get("/specs-list")
async def list_specs():
    """List all available technical sheet images"""
    if not os.path.exists(SPECS_DIR):
        return []
    files = os.listdir(SPECS_DIR)
    # Only images
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = [f for f in files if os.path.splitext(f)[1].lower() in valid_exts]
    return images

@app.post("/upload-inventory")
async def upload_inventory(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")
    
    file_path = os.path.join(STORAGE_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    rotate_inventories()
    return {"message": "Inventario cargado con éxito.", "filename": file.filename}

@app.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Formato no soportado.")
    file_path = os.path.join(SPECS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Ficha técnica recibida."}

@app.get("/knowledge")
async def get_knowledge():
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/update-knowledge")
async def update_knowledge(entry: dict):
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        knowledge = json.load(f)
    found = False
    for i, item in enumerate(knowledge):
        if item.get("sku") == entry.get("sku"):
            knowledge[i] = entry
            found = True
            break
    if not found:
        knowledge.append(entry)
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=4)
    return {"message": "OK"}

@app.get("/api/pool-stats")
async def get_pool_stats():
    """Get AI pool performance statistics"""
    if ai_pool:
        return ai_pool.get_stats()
    else:
        return {
            "error": "AI Pool not initialized",
            "fallback_mode": "single_gemini_model"
        }

SYNONYMS = {
    "port": "portatil", "portatil": "prt", "portatiles": "prt", "laptop": "prt", "laptops": "prt",
    "hp": "hewp", "hewlett": "hewp", "packard": "hewp", "ng": "negro", "ngr": "negro",
    "bl": "blanco", "blnc": "blanco", "cel": "celular", "celulares": "celular",
    "tel": "telefono", "telefonos": "celular", "aud": "audifonos", "audifono": "audifonos",
    "smrt": "smart", "watch": "reloj", "sw": "reloj", "tablet": "tab", "tablets": "tab",
    "ryzen": "rzn", "intel": "ic", "core": "ic", "ram": "g", "gb": "g"
}

def resolve_spec_match(mat_id, subprod, available_specs, manual_map):
    """Hybrid logic to match inventory item with a spec file."""
    subprod_upper = str(subprod).upper()
    mat_id_str = str(mat_id)
    
    # 1. Manual Mapping (Priority 1)
    for key, val in manual_map.items():
        if key.upper() in subprod_upper or key == mat_id_str:
            if isinstance(val, dict):
                for size_key, fname in val.items():
                    # Handle size matches like "50" in "TV 50C69B..."
                    if size_key in subprod_upper:
                        return fname
            return val
            
    # 2. Exact Material ID Match (Priority 2)
    for f in available_specs:
        if mat_id_str in f:
            return f
            
    # 3. Keyword Intersection Match (Priority 3)
    def get_intersection_score(p_name, f_name):
        # Noise words to ignore
        noise = {"ngr", "grs", "slv", "sams", "xiao", "tv", "tab", "cel", "lat", 
                 "negro", "gris", "silver", "tcl", "pana", "huaw", "honor", "motorola", 
                 "apple", "iphone", "pro", "max", "lit", "lite"}
        p_words = set(re.findall(r'\w+', p_name.lower())) - noise
        f_words = set(re.findall(r'\w+', f_name.lower())) - noise
        return len(p_words.intersection(f_words))

    best_file = None
    best_score = 0
    for f in available_specs:
        score = get_intersection_score(subprod_upper, f)
        if score > best_score and score >= 2:
            best_score = score
            best_file = f
            
    return best_file

@app.get("/specs-mapping")
async def get_specs_mapping():
    """Endpoint for frontend to get the resolved MaterialID -> Filename map."""
    df = await get_latest_inventory()
    if df is None: return {}
    
    try:
        available_specs = os.listdir(SPECS_DIR)
        with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
            manual_map = json.load(f)
    except:
        available_specs = []
        manual_map = {}

    resolved = {}
    for _, item in df.iterrows():
        match = resolve_spec_match(item['Material'], item['Subproducto'], available_specs, manual_map)
        if match:
            resolved[str(item['Material'])] = match
    return resolved

@app.get("/chat")
async def chat(query: str):
    df = await get_latest_inventory()
    if df is None:
        # Check if there are ANY pdfs in storage to give a better message
        import glob
        pdf_count = len(glob.glob(os.path.join(STORAGE_DIR, "*.pdf")))
        if pdf_count == 0:
            return {"response": "No encontré archivos de inventario en mi carpeta de almacenamiento. Por favor, asegúrate de haber subido el PDF a `backend/storage` en GitHub."}
        else:
            return {"response": "Encontré el archivo de inventario pero tuve un problema procesándolo. Por favor, verifica que el PDF tenga el formato correcto o intenta subirlo de nuevo."}

    # Logging helper first!
    def log_debug(msg):
        with open("chat_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
    
    log_debug(f"QUERY RECIBIDA (Original): {query}")

    # Normalization helper for comparison
    def normalize_str(s):
        return str(s).lower().strip() if s else ""
        
    # Translate nomenclature
    # Replace "pulgadas" with " (with no space if possible)
    query_clean = query.lower().replace(" pulgadas", "\"").replace(" pulgada", "\"").replace(" pulgs", "\"")
    query_clean = query_clean.replace("pulgadas", "\"").replace("pulgada", "\"").replace("pulgs", "\"")
    # Technical nomenclature mapping in query string before split
    query_clean = query_clean.replace("ram", "g").replace("gb", "g")
    
    raw_keywords = query_clean.split()
    stop_words = ["de", "con", "el", "la", "los", "las", "un", "una", "en", "para", "por"]
    
    valid_keywords = []
    for k in raw_keywords:
        if k in stop_words or k == "\"": continue
        # Normalize common synonyms/plurals BEFORE removing 's'
        if k in ["televisor", "televisores", "television", "televisiones"]: 
            valid_keywords.append("tv")
            continue
        if k in ["tablet", "tablets", "tableta", "tabletas"]: 
            valid_keywords.append("tab")
            continue
        if k in ["patineta", "patinetas", "scooter", "scooters"]: 
            valid_keywords.append("ptn")
            continue
            
        # Generic plural removal for other words
        k_norm = k.rstrip('s') if k.endswith('s') and len(k) >= 3 else k
        
        if len(k_norm) >= 2 or k_norm.isdigit() or '\"' in k_norm or k_norm in ["tv", "sw", "bt", "tab", "ptn"]:
            valid_keywords.append(k_norm)
    
    # SMART TV SIZE DETECTION: If 'tv' is in keywords and there's a number, convert it to inch format
    if "tv" in valid_keywords:
        for i, k in enumerate(valid_keywords):
            if k.isdigit() and '\"' not in k:
                valid_keywords[i] = k + '\"'  # Convert '65' to '65"'
    
    log_debug(f"Keywords válidas final: {valid_keywords}")
    
    # Special translation: "50 pulgadas" -> "50\"" if looking for TV
    # For keyword search, we just ensure "50" or "50\"" is present
    
    # 1. Try simple search first
    results = pd.DataFrame() # Empty by default
    fast_path_used = False
    
    if valid_keywords:
        # For TV size searches, only look for inch measurements in Subproducto (not prices/IDs)
        def matches_keywords(row):
            for k in valid_keywords:
                # If it's an inch measurement (e.g., '65"'), only search in Subproducto
                if '\"' in k:
                    if k not in normalize_str(row["Subproducto"]):
                        return False
                # For other keywords, search in all relevant fields
                elif not (k in normalize_str(row["Subproducto"]) or 
                         k in normalize_str(row["Material"]) or 
                         k in normalize_str(row["modelo_limpio"]) or
                         k in normalize_str(row["especificaciones"]) or
                         (k == "ptn" and any(s in normalize_str(row["Subproducto"]) for s in ["ptn", "ptnet", "patinet", "scter"]))):
                    return False
            return True
        
        mask = df.apply(matches_keywords, axis=1)
        direct_matches = df[mask]
        log_debug(f"FAST PATH: Found {len(direct_matches)} matches")
        
        if 0 < len(direct_matches) < 100:
            log_debug("FAST PATH: EXECUTED")
            results = direct_matches
            fast_path_used = True
            intent = {"intencion_general": "Búsqueda directa por palabras clave"}

    if not fast_path_used:
        # --- STEP 1: Understand Intent (Slow AI Path) ---
        # We use a specialized prompt to map the query to our normalized fields
        intent_prompt = f"""
        Eres un experto en clasificar intenciones de búsqueda para un inventario de tecnología.
        
        CAMPOS DISPONIBLES EN BD:
        - categoria: (TV, Celular, Laptop, Reloj, Audífonos, Parlante, Patineta, Tablet, Accesorio, Otro)
        - marca: (Samsung, Apple, HP, Lenovo, Xiaomi, Huawei, Honor, Sony, etc.)
        - modelo: (Referencia específica o palabras clave del producto)
        
        CONSULTA USUARIO: "{query}"
        
        TU TAREA:
        Extrae los valores para filtrar el DataFrame. 
        REGLA CRÍTICA PARA TV: Si el usuario busca pulgadas (ej: "50 pulgadas", "de 43", "55"), el campo 'modelo' DEBE incluir el número seguido de comilla doble (ej: '50"', '43"', '55"') para coincidir con la nomenclatura del inventario.
        
        EJEMPLOS:
        - "televisores samsung 50 pulgadas" -> {{"categoria": "TV", "marca": "Samsung", "modelo": "50\\""}}
        - "smart tv 43" -> {{"categoria": "TV", "marca": null, "modelo": "43\\""}}
        - "iphone 15" -> {{"marca": "Apple", "modelo": "iphone 15", "categoria": "Celular"}}
        
        Responde ÚNICAMENTE en JSON:
        {{
            "categoria": "Valor exacto de la lista o null",
            "marca": "Valor o null",
            "modelo": "Valor o null",
            "intencion_general": "Resumen breve de lo que busca"
        }}
        """
        
        intent = {"categoria": None, "marca": None, "modelo": None}
        try:
            if not ai_pool:
                print("WARNING: AI Pool not available, skipping intent analysis")
            else:
                with open("debug_log.txt", "a", encoding="utf-8") as f:
                     f.write(f"DEBUG INTENT PROMPT LEN: {len(intent_prompt)}\n")
                intent_response_text = await ai_pool.generate(intent_prompt)
                intent_text = intent_response_text
                # Clean markdown
                if "```json" in intent_text:
                    intent_text = intent_text.split("```json")[1].split("```")[0].strip()
                elif "```" in intent_text:
                    intent_text = intent_text.split("```")[1].split("```")[0].strip()
                intent = json.loads(intent_text)
        except Exception as e:
            print(f"Error Intent AI: {e}")

        print(f"Intención detectada: {intent}")

        # --- STEP 2: Filter Data (AI Path) ---
        results = df.copy()
        
        # 1. Filter by Category (Strict-ish but inclusive for N/A)
        if intent.get("categoria"):
            cat_filter = intent["categoria"].lower()
            # Inclusive: Match if category is correct OR if item is N/A/Otro but name contains category string
            def matches_category(row):
                item_cat = normalize_str(row["categoria"])
                item_name = normalize_str(row["Subproducto"])
                # Case 1: Category matches exactly
                if cat_filter in item_cat or item_cat in cat_filter:
                    return True
                # Case 2: Item is uncategorized but name contains the category关键词 (e.g. "TV")
                if item_cat in ["n/a", "otro", "", "none"]:
                    # map "tv" to "television" etc for better coverage
                    synonyms = [cat_filter]
                    if cat_filter == "tv": synonyms.extend(["tv", "televis", "smart"])
                    if cat_filter == "audífonos": synonyms.extend(["aud", "auric", "buds"])
                    if cat_filter == "celular": synonyms.extend(["cel", "tel", "phone", "iphone", "galaxy"])
                    if cat_filter == "tablet": synonyms.extend(["tablet", "tab", "ipad"])
                    if cat_filter == "patineta": synonyms.extend(["patine", "ptnta", "ptneta", "scter", "scooter"])
                    return any(s in item_name for s in synonyms)
                return False
                
            results = results[results.apply(matches_category, axis=1)]
            log_debug(f"AI PATH: After Categoria: {len(results)}")

        if intent.get("marca") and not results.empty:
            brand_filter = intent["marca"].lower()
            results = results[results["marca"].apply(lambda x: brand_filter in normalize_str(x) or normalize_str(x) in brand_filter)]
            log_debug(f"AI PATH: After Marca: {len(results)}")

        if intent.get("modelo") and not results.empty:
            mod_raw = normalize_str(intent["modelo"]).replace("pulgadas", "\"").replace("pulgada", "\"").replace("pulgs", "\"")
            mod_keywords = [w for w in mod_raw.split() if len(w) > 1 and w != "\""]
            if mod_keywords:
                # Must match ALL keywords from the model intent
                mask = results.apply(lambda row: 
                                     all(k in normalize_str(row["Subproducto"]) or 
                                         k in normalize_str(row["Material"]) or
                                         k in normalize_str(row["modelo_limpio"]) or
                                         k in normalize_str(row["especificaciones"]) for k in mod_keywords), axis=1)
                results = results[mask]
                log_debug(f"AI PATH: After Modelo ({mod_keywords}): {len(results)}")

        if results.empty and valid_keywords:
            log_debug(f"AI PATH empty for intent {intent}, falling back to keywords {valid_keywords}")
            # BROADER KEYWORD FALLBACK (+ specifically check for TV symbols if category was TV)
            if intent.get("categoria") == "TV":
                # Ensure we look for the " symbol even in fallback
                tv_keywords = [k for k in valid_keywords if len(k) >= 2] + ["\""]
                mask = df.apply(lambda row: all(k in normalize_str(row["Subproducto"]) or k in normalize_str(row["especificaciones"]) for k in tv_keywords), axis=1)
            else:
                mask = df.apply(lambda row: all(k in normalize_str(row["Subproducto"]) or k in normalize_str(row["especificaciones"]) for k in valid_keywords if len(k) >= 2 or k.isdigit()), axis=1)
            results = df[mask]
            log_debug(f"Fallback results: {len(results)}")

    # --- STEP 3: Context for CLEO ---
    inventory_context = ""
    if not results.empty:
        # Get list of available specs for matching
        try:
            available_specs = os.listdir(SPECS_DIR)
            with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
                manual_map = json.load(f)
        except:
            available_specs = []
            manual_map = {}

        # DEDUPLICATION: Keep only the entry with highest stock for each Material ID
        results = results.sort_values(by=["CantDisponible"], ascending=False)
        results = results.drop_duplicates(subset=["Material"], keep="first")
        log_debug(f"After deduplication: {len(results)} unique materials")
        
        # Prioritize by Stock (descending) first, then by Price (descending)
        results = results.sort_values(by=["CantDisponible", "Precio Contado"], ascending=[False, False]).head(50)
        
        for _, item in results.iterrows():
            # Check if spec exists using robust hybrid logic
            match = resolve_spec_match(item['Material'], item['Subproducto'], available_specs, manual_map)
            ficha_tag = "SI" if match else "NO"

            # Format price nicely
            try:
                precio = f"${float(item['Precio Contado']):,.0f}"
            except:
                precio = str(item['Precio Contado'])

            specs = item.get('especificaciones', 'N/A')
            if specs == 'N/A': specs = ""
            
            # Construct readable line with FICHA tag
            line = f"- [ID: {item['Material']}] MODELO: {item['Subproducto']} | FICHA: {ficha_tag} | CATEGORIA: {item['categoria']} | MARCA: {item['marca']} | DESC: {specs} | STOCK: {int(item['CantDisponible'])} | PRECIO CONTADO: {precio}\n"
            inventory_context += line
    else:
        inventory_context = "No se encontraron productos que coincidan exactamente con la búsqueda."

    print(f"Contexto generado ({len(results)} items):")
    
    # SAFETY: If context is empty, give Cleo a generic "No found" instruction
    # to avoid empty prompt issues or hallucinations
    if not inventory_context:
        inventory_context = "No se encontraron productos en el inventario para esta búsqueda."

    full_prompt = f"""
    {CLEO_PROMPT}

    DATOS DEL INVENTARIO ENCONTRADO (Usa esta información para responder):
    {inventory_context}

    PREGUNTA DEL USUARIO:
    "{query}"
    
    REGLA: Si no hay inventario, sugiere productos similares si los ves, o di que no hay stock disponible.
    """

    try:
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG PROMPT LEN: {len(full_prompt)}\n")
            f.write(f"DEBUG PROMPT START: {full_prompt[:100]}...\n")

        # Use AI Pool if available, otherwise fallback to single model
        if ai_pool:
            response_text = await ai_pool.generate(full_prompt)
            return {"response": response_text}
        else:
            response = model.generate_content(full_prompt)
            return {"response": response.text.strip()}
    except Exception as e:
        print(f"Error Cleo: {e}")
        import traceback
        traceback.print_exc()
        with open("debug_log.txt", "a") as f:
            f.write(f"DEBUG CHAT ERROR: {e}\n")
            f.write(f"{traceback.format_exc()}\n")
        
        # Check if it's a quota error
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return {"response": "Cleo ha alcanzado el límite de consultas. Por favor, espera unos minutos o contacta al administrador para añadir más APIs."}
        
        return {"response": "Lo siento, tuve un problema analizando el inventario."}

if __name__ == "__main__":
    print("Iniciando servidor Cleo AI (Reload desactivado para estabilidad)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
