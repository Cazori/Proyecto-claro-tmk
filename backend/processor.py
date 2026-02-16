import pdfplumber
import pandas as pd
import os
import glob
import re
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# AI Pool will be injected from main.py
_ai_pool = None

def set_ai_pool(pool):
    """Set the AI pool instance for normalization"""
    global _ai_pool
    _ai_pool = pool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
PROCESSED_DATA_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
NORMALIZATION_CACHE_FILE = os.path.join(STORAGE_DIR, "normalization_cache.json")
METADATA_FILE = os.path.join(STORAGE_DIR, "processing_metadata.json")
MAX_FILES = 5

async def normalize_products_batch(descriptions):
    """
    Uses AI Pool to categorize and extract attributes from a list of unique product descriptions.
    Robust to 429 Quota errors through multi-provider fallback.
    """
    if not descriptions:
        return {}
    
    if not _ai_pool:
        print("WARNING: AI Pool not initialized, skipping normalization for this batch")
        return {}

    prompt = """
    Analiza esta lista de descripciones de productos tecnológicos.
    Para cada uno, extrae:
    - categoria: (TV, Celular, Laptop, Reloj, Audífonos, Parlante, Patineta, Tablet, Accesorio, Otro)
    - marca: La marca (Samsung, Huawei, etc.)
    - modelo_limpio: Nombre del modelo
    - especificaciones: Características clave
    Responde ÚNICAMENTE en JSON con las descripciones originales como llaves.
    LISTA: """ + json.dumps(descriptions)

    # Retry logic with AI Pool
    import time
    for attempt in range(3):
        try:
            response_text = await _ai_pool.generate(prompt)
            # Clean markdown if present
            raw_text = response_text
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(raw_text)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                print(f"Quota exceeded on attempt {attempt+1}/3. AI Pool will try next provider...")
                time.sleep(5)  # Shorter wait since pool handles rotation
            else:
                print(f"Error AI Pool: {err_msg}")
                break
    return {}

def rule_based_normalization(desc):
    """Fallback logic for common brands and categories using keywords"""
    desc_upper = desc.upper()
    res = {"categoria": "N/A", "marca": "N/A", "modelo_limpio": desc, "especificaciones": ""}
    
    # Category detection
    if any(k in desc_upper for k in ["TV", "TELEVIS"]): res["categoria"] = "TV"
    elif any(k in desc_upper for k in ["PRT", "PORT", "LAPTOP"]): res["categoria"] = "Laptop"
    elif any(k in desc_upper for k in ["TAB", "IPAD"]): res["categoria"] = "Tablet"
    elif any(k in desc_upper for k in ["CEL", "SMARTPHONE", "MOTO", "IPHONE"]): res["categoria"] = "Celular"
    elif any(k in desc_upper for k in ["PATINETA"]): res["categoria"] = "Patineta"
    elif any(k in desc_upper for k in ["AUD", "BUDS", "AURIC"]): res["categoria"] = "Audífonos"
    elif any(k in desc_upper for k in ["WATCH", "SMRT", "CLOCK"]): res["categoria"] = "Reloj"
    
    # Brand detection
    brands = {
        "SAMS": "Samsung", "SAMSUNG": "Samsung",
        "HUAW": "Huawei", "HUAWEI": "Huawei",
        "MOT": "Motorola", "MOTOROLA": "Motorola",
        "XIAO": "Xiaomi", "XIAOMI": "Xiaomi",
        "HEWP": "HP", "HP": "HP",
        "LENO": "Lenovo", "LENOVO": "Lenovo",
        "ASUS": "Asus",
        "APPL": "Apple", "IPHONE": "Apple", "IPAD": "Apple", "APPLE": "Apple",
        "TCL": "TCL",
        "NIU": "NIU",
        "HONOR": "Honor"
    }
    for k, v in brands.items():
        if f" {k}" in f" {desc_upper}" or f"{k} " in f"{desc_upper} " or desc_upper.endswith(k):
            res["marca"] = v
            break
            
    return res

async def process_inventory_pdf(file_path):
    """
    Extracts data from PDF and normalizes it using AI for categorization/specs.
    Returns a DataFrame.
    """
    try:
        data = []
        if not os.path.exists(file_path):
            return None

        with pdfplumber.open(file_path) as pdf:
            page_bodega = "CEM Bogotá - ZF" # Default
            
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                # Find bodega name in page header
                bodega_match = re.search(r"CEM\s+([\w\s-]+?)(?:\s+[CH]\d{3}|\d{7})", text)
                if bodega_match:
                    page_bodega = bodega_match.group(1).strip()
                
                # Process line by line to allow greedy name capture safely
                lines = text.split('\n')
                for line in lines:
                    # Robust Pattern: ID -> Name -> Number -> Number -> ... -> Aplica
                    pattern = r"(\d{7})\s*(.+)\s+(\d+)\s+(\d+).*?Aplica\s+\$.*?(\d[\d\.\s-]*(?:\d|$))"
                    match = re.search(pattern, line)
                    
                    if match:
                        material = match.group(1)
                        subproducto = match.group(2).strip()
                        stock = match.group(3) # Group 3 (Total)
                        price_raw = match.group(5)
                        
                        precio_clean = re.sub(r'[^\d]', '', price_raw)
                        if len(precio_clean) > 8:
                            precio_clean = precio_clean[:7]
                        
                        data.append({
                            "Bodega": page_bodega,
                            "Material": material,
                            "Subproducto": subproducto,
                            "CantDisponible": float(stock) if stock else 0,
                            "Precio Contado": float(precio_clean) if precio_clean else 0
                        })
        
        print(f"DEBUG: Total items pre-filter: {len(data)}")
        if not data:
            return None

        df = pd.DataFrame(data)
        
        # FILTER: STRICT BOGOTA ONLY (Ingestion Level)
        if not df.empty and "Bodega" in df.columns:
            df = df[df["Bodega"].astype(str).str.upper().str.contains("BOGOT")]
            print(f"Filtrado estricto: BOGOTÁ. Items restantes: {len(df)}")
        
        df = df.drop_duplicates(subset=["Material", "Subproducto", "CantDisponible"])
        
        # --- Semantic Normalization ---
        normalization_cache = {}
        if os.path.exists(NORMALIZATION_CACHE_FILE):
            try:
                with open(NORMALIZATION_CACHE_FILE, "r", encoding="utf-8") as f:
                    normalization_cache = json.load(f)
            except: pass
        else:
            with open(NORMALIZATION_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)

        unique_products = df["Subproducto"].unique().tolist()
        
        def get_attr(desc, attr):
            norm = normalization_cache.get(desc, {})
            val = norm.get(attr.lower()) or norm.get(attr.capitalize()) or norm.get(attr)
            
            if not val or val == "N/A":
                # Fallback to rule-based
                rb = rule_based_normalization(desc)
                val = rb.get(attr.lower()) or "N/A"
            return str(val)

        # Only normalize what's NOT in the cache
        to_normalize = [p for p in unique_products if p not in normalization_cache]
        
        if to_normalize:
            print(f"Normalizando {len(to_normalize)} nuevos productos únicos...")
            for i in range(0, len(to_normalize), 5):
                batch = to_normalize[i:i+5]
                # AWAIT the async normalization
                normalized_batch = await normalize_products_batch(batch)
                if normalized_batch:
                    normalization_cache.update(normalized_batch)
                    with open(NORMALIZATION_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(normalization_cache, f, indent=4)
                    
        # Final mapping
        df["categoria"] = df["Subproducto"].apply(lambda x: get_attr(x, "categoria"))
        df["marca"] = df["Subproducto"].apply(lambda x: get_attr(x, "marca"))
        df["modelo_limpio"] = df["Subproducto"].apply(lambda x: get_attr(x, "modelo_limpio"))
        df["especificaciones"] = df["Subproducto"].apply(lambda x: get_attr(x, "especificaciones"))

        df.to_json(PROCESSED_DATA_FILE, orient="records", force_ascii=False, indent=4)
        
        # Save metadata to track which file was processed
        try:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_processed_file": os.path.basename(file_path)}, f)
        except: pass
        
        print(f"Éxito: {len(df)} ítems procesados.")
        return df

    except Exception as e:
        print(f"Error en procesamiento híbrido: {e}")
        return None

def rotate_inventories():
    """
    Keeps only the most recent 5 files and cleans up processed data to force re-processing.
    """
    if os.path.exists(PROCESSED_DATA_FILE):
        try:
            os.remove(PROCESSED_DATA_FILE)
            print("Datos procesados invalidados (se re-generarán en la próxima consulta).")
        except: pass

    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if len(files) <= MAX_FILES:
        return

    files.sort(key=os.path.getmtime)
    for i in range(len(files) - MAX_FILES):
        try:
            os.remove(files[i])
        except: pass

async def get_latest_inventory():
    """
    Returns the most recent processed DataFrame. 
    Uses metadata to detect if the latest PDF has changed.
    """
    pdf_files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if not pdf_files:
        return None
        
    # Sort by mtime then name to find the "newest"
    pdf_files.sort(key=lambda x: (os.path.getmtime(x), x), reverse=True)
    latest_pdf = pdf_files[0]
    latest_pdf_name = os.path.basename(latest_pdf)
    
    should_reprocess = True
    
    # Check if we already processed this exact file
    if os.path.exists(PROCESSED_DATA_FILE) and os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                if metadata.get("last_processed_file") == latest_pdf_name:
                    should_reprocess = False
        except:
            pass

    if should_reprocess:
        print(f"Detectado cambio o nuevo archivo: {latest_pdf_name}. Re-procesando...")
        return await process_inventory_pdf(latest_pdf)
    
    try:
        return pd.read_json(PROCESSED_DATA_FILE)
    except:
        return await process_inventory_pdf(latest_pdf)
