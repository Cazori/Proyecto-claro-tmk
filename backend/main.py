from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks

# ... (keep other imports)

async def background_inventory_processing(file_path:str, filename: str):
    """Heavy lifting done in the background to avoid HTTP timeouts"""
    try:
        from processor import process_inventory_pdf, rotate_inventories
        rotate_inventories()
        await process_inventory_pdf(file_path)
        # Cloud Storage Upload (Raw PDF)
        await upload_inventory_pdf_to_supabase(file_path, filename)
        print(f"✓ Inventario {filename} procesado y sincronizado en segundo plano.")
    except Exception as e:
        print(f"✗ ERROR en procesamiento de fondo: {e}")

@app.post("/upload-inventory")
async def upload_inventory(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")
    
    file_path = os.path.join(STORAGE_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add to background tasks
    background_tasks.add_task(background_inventory_processing, file_path, file.filename)
    
    return {
        "message": "Archivo recibido. Cleo está actualizando el inventario en segundo plano. Podrás ver los cambios en unos segundos.",
        "filename": file.filename
    }

@app.get("/inventory-metadata")
async def get_inventory_metadata():
    inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
    if os.path.exists(inv_file):
        last_mod = os.path.getmtime(inv_file)
        dt = datetime.fromtimestamp(last_mod)
        return {"last_update": dt.isoformat(), "status": "active"}
    return {"last_update": None, "status": "no_data"}

@app.get("/quotas")
async def get_quotas_mapping():
    """Returns the mapping of Material ID -> Installment Plans"""
    mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
    if os.path.exists(mapping_file):
        with open(mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.post("/upload-quotas")
async def upload_quotas(file: UploadFile = File(...)):
    """Upload cuotas.xlsx and auto-process it to generate quota_mapping.json"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .xlsx")
    
    quotas_path = os.path.join(STORAGE_DIR, "cuotas.xlsx")
    with open(quotas_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Auto-process immediately
    try:
        from process_quotas import process_quotas
        process_quotas()
        mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            return {"message": f"Cuotas procesadas exitosamente. {len(result)} equipos mapeados.", "count": len(result)}
        return {"message": "Archivo subido pero no se pudo procesar.", "count": 0}
    except Exception as e:
        return {"message": f"Archivo subido. Error al procesar: {str(e)}", "count": 0}

@app.post("/process-quotas")
async def trigger_process_quotas():
    """Re-run quota processing with existing cuotas.xlsx"""
    quotas_path = os.path.join(STORAGE_DIR, "cuotas.xlsx")
    if not os.path.exists(quotas_path):
        raise HTTPException(status_code=404, detail="No hay archivo cuotas.xlsx en el servidor. Sube uno primero.")
    try:
        from process_quotas import process_quotas
        process_quotas()
        mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            return {"message": f"Cuotas reprocesadas. {len(result)} equipos mapeados.", "count": len(result)}
        return {"message": "Error: no se generó el archivo de mapeo.", "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Formato no soportado.")
    
    file_path = os.path.join(SPECS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Cloud Storage Upload
    import asyncio
    asyncio.create_task(upload_spec_to_supabase(file_path, file.filename))
    
    return {"message": "Ficha técnica recibida y sincronizada con la nube."}

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

# In-request cache for spec resolution to avoid redundant calls
_spec_match_cache = {}

def resolve_spec_match(mat_id, subprod, available_specs, manual_map):
    """Hybrid logic to match inventory item with a spec file."""
    subprod_upper = str(subprod).upper()
    mat_id_str = str(mat_id)

    # Check cache first
    cache_key = f"{mat_id_str}:{subprod_upper}"
    if cache_key in _spec_match_cache:
        return _spec_match_cache[cache_key]

    for key, val in manual_map.items():
        if key.upper() in subprod_upper or key == mat_id_str:
            if isinstance(val, dict):
                for size_key, fname in val.items():
                    if size_key in subprod_upper:
                        _spec_match_cache[cache_key] = fname
                        return fname
            _spec_match_cache[cache_key] = val
            return val
            
    # 2. Exact Material ID Match (Priority 2)
    # Only match if ID is long enough (prevents accidental matches with model numbers like "4" or "1")
    if len(mat_id_str) >= 4:
        for f in available_specs:
            if re.search(rf"\b{mat_id_str}\b", f):
                _spec_match_cache[cache_key] = f
                return f
            
    # --- SMART VARIANT GUARD ---
    def check_variant_mismatch(p_name, f_name):
        # 1. Normalize categories
        p_norm = p_name.upper().replace("TELEVISOR", "TV").replace("TABLET", "TAB").replace("CELULAR", "CEL")
        f_norm = f_name.upper().replace("TELEVISOR", "TV").replace("TABLET", "TAB").replace("CELULAR", "CEL")
        
        p_clean_str = re.sub(r'[^A-Z0-9\s]', ' ', p_norm)
        f_clean_str = re.sub(r'[^A-Z0-9\s]', ' ', f_norm)
        
        p_words = set(p_clean_str.split())
        f_words = set(f_clean_str.split())
        
        # 2. Critical Version Keywords (Hard mismatch)
        # Handle cases where keywords might be concatenated (e.g., S10Lite)
        versions = ["PRO", "ULTRA", "MAX", "PLUS", "LITE", "5G", "MINI"]
        for v in versions:
            in_p = v in p_words
            # Also check if version is part of a word in filename (common in specs)
            in_f = v in f_words or any(v in word for word in f_words)
            if in_p != in_f:
                return True
                
        # 3. Category Check (Soft mismatch)
        categories = ["TV", "TAB", "CEL"]
        p_cat = next((c for c in categories if c in p_words), None)
        f_cat = next((c for c in categories if c in f_words), None)
        if p_cat and f_cat and p_cat != f_cat:
            return True
                
        # 3. Smart Numeric Check — only block if filename has significant numbers absent from product
        # This prevents false negatives: SE11 has SKU codes like "8G", "09" that are not in "se11"
        f_clean_str_local = re.sub(r'[^A-Z0-9\s]', ' ', f_norm)
        p_clean_str_local = re.sub(r'[^A-Z0-9\s]', ' ', p_norm)
        f_sig_nums = {n for n in re.findall(r'\d+', f_clean_str_local) if len(n) >= 2}
        p_nums_all = set(re.findall(r'\d+', p_clean_str_local))
        if f_sig_nums and not f_sig_nums.intersection(p_nums_all):
            return True
                
        return False

    # 3. Robust Keyword Scoring (Priority 3)
    noise = {"ngr", "grs", "slv", "negro", "gris", "silver", "pulg", "pulgadas", "inches", "smart"}
    clean_p_name = re.sub(r'[^A-Z0-9\s]', ' ', subprod_upper)
    p_words = [w for w in clean_p_name.lower().split() if (len(w) > 2 or w.isdigit()) and w not in noise]
    
    best_file = None
    max_score = 0
    
    for f in available_specs:
        if check_variant_mismatch(subprod_upper, f):
            continue

        f_name_clean = re.sub(r'[^A-Z0-9\s]', ' ', f.upper().split('.')[0])
        f_words = f_name_clean.lower().split()
        
        score = 0
        for pw in p_words:
            if pw in f_words:
                score += 5
            elif any(pw in fw for fw in f_words):
                score += 2
        
        if score > max_score and score >= 10:
            max_score = score
            best_file = f
            
    if best_file:
        _spec_match_cache[cache_key] = best_file
        return best_file

    # 4. Semantic Matching (Priority 4)
    # Use embeddings service with a higher safety threshold
    semantic_match = embeddings_service.find_best_match(subprod_upper, available_specs, threshold=0.82)
    
    if semantic_match:
        if not check_variant_mismatch(subprod_upper, semantic_match):
            _spec_match_cache[cache_key] = semantic_match
            return semantic_match
    
    _spec_match_cache[cache_key] = None
    return None

@app.get("/specs-mapping")
async def get_specs_mapping():
    """Endpoint for frontend to get the resolved MaterialID -> Filename map."""
    df = await get_latest_inventory()
    if df is None: return {}
    
    # 1. Try to serve from persistent cache if valid
    cache_file = os.path.join(STORAGE_DIR, "specs_resolved_cache.json")
    inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
    
    try:
        if os.path.exists(cache_file) and os.path.exists(inv_file):
            cache_mtime = os.path.getmtime(cache_file)
            inv_mtime = os.path.getmtime(inv_file)
            
            # If cache is newer than inventory, it should be valid
            if cache_mtime > inv_mtime:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception as e:
        print(f"Cache read error: {e}")

    # 2. Re-calculate if cache is invalid or missing
    print("Recalculando mapeo de imágenes (Caché inválida o ausente)...")
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
            
    # Save to persistent cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(resolved, f, indent=4)
    except Exception as e:
        print(f"Cache write error: {e}")

    return resolved

@app.post("/generate-tip")
async def generate_tip(data: dict):
    model_name = data.get("model")
    specs = data.get("specs")
    if not model_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del modelo.")
    
    prompt = f"""
    Eres un experto en ventas de tecnología para Claro. 
    Crea un "Tip de Venta" o "Speech" breve (máximo 20 palabras) para este producto:
    PRODUCTO: {model_name}
    ESPECIFICACIONES: {specs if specs else 'No disponibles'}
    
    El tip debe ser persuasivo, técnico pero fácil de entender, y resaltar un beneficio clave.
    Responde ÚNICAMENTE con el texto del tip, sin comillas ni introducciones.
    """
    
    try:
        if ai_pool:
            response = await ai_pool.generate(prompt)
            return {"tip": response.strip()}
        else:
            # Fallback to single model if pool is not initialized
            # (Note: 'model' would need to be imported or handled if pool fails)
            return {"tip": "Destaca la excelente relación calidad-precio y la garantía de Claro."}
    except Exception as e:
        print(f"Error generando tip: {e}")
        return {"tip": "Destaca la excelente relación calidad-precio y la garantía de Claro."}

@app.get("/knowledge")
async def get_knowledge():
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

@app.post("/update-knowledge")
async def update_knowledge(entry: dict):
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update or add
        sku = entry.get("sku")
        found = False
        for i, item in enumerate(data):
            if item.get("sku") == sku:
                data[i] = entry
                found = True
                break
        
        if not found:
            data.append(entry)
            
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return {"message": "Conocimiento actualizado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/find-product")
async def find_product(material: str):
    try:
        df = await get_latest_inventory()
        # Filter by material
        product = df[df['Material'].astype(str) == str(material)]
        if not product.empty:
            item = product.iloc[0].to_dict()
            # Clean for JSON
            cleaned_item = {k: (None if pd.isna(v) else v) for k, v in item.items()}
            return cleaned_item
        return {"error": "Producto no encontrado"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/apply-auto-tips")
async def apply_auto_tips(data: dict):
    category = data.get("category")
    tip = data.get("tip")
    if not category or not tip:
        raise HTTPException(status_code=400, detail="Categoría y tip son obligatorios.")
    
    try:
        df = await get_latest_inventory()
        # Filter products by category
        mask = df['categoria'].astype(str).str.upper() == category.upper()
        targets = df[mask]
        
        # Load current expert knowledge
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            expert_data = json.load(f)
        
        applied_count = 0
        for _, row in targets.iterrows():
            sku = str(row['Material'])
            # Only apply if not already in expert knowledge or has no tip
            existing = next((item for item in expert_data if item.get("sku") == sku), None)
            if existing:
                if not existing.get("tip_venta") or existing.get("tip_venta") == "-":
                    existing["tip_venta"] = tip
                    applied_count += 1
            else:
                expert_data.append({
                    "sku": sku,
                    "model": row['Subproducto'],
                    "specs": row.get('especificaciones', '-'),
                    "tip_venta": tip
                })
                applied_count += 1
        
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(expert_data, f, indent=4, ensure_ascii=False)
            
        return {"message": "Tips aplicados correctamente.", "applied": applied_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat")
async def chat(query: str):
    df = await get_latest_inventory()
    if df is None:
        return {"response": "Sube un inventario PDF para comenzar."}

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
            # Load expert knowledge for manual tips
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                expert_data = json.load(f)
                expert_tips = {item['sku']: item.get('tip_venta') for item in expert_data if item.get('tip_venta')}
        except:
            available_specs = []
            manual_map = {}
            expert_tips = {}

        # DEDUPLICATION: Keep only the entry with highest stock for each Material ID
        results = results.sort_values(by=["CantDisponible"], ascending=False)
        results = results.drop_duplicates(subset=["Material"], keep="first")
        log_debug(f"After deduplication: {len(results)} unique materials")
        
        # Prioritize by Stock (descending) first, then by Price (descending)
        # We limit to 20 products for faster AI processing in call center environments
        results = results.sort_values(by=["CantDisponible", "Precio Contado"], ascending=[False, False]).head(20)
        
        for _, item in results.iterrows():
            # Check image existence using robust hybrid logic
            match = resolve_spec_match(item['Material'], item['Subproducto'], available_specs, manual_map)
            
            # Determine if we have an image (vs a PDF or nothing)
            has_image = "NO"
            if match:
                is_img_ext = any(match.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"])
                if is_img_ext:
                    has_image = "SI"
            
            # For backward compatibility with mapping or direct Material.jpg
            if has_image == "NO":
                if str(item['Material']) in manual_map:
                    has_image = "SI" # Mapping exists
                elif f"{item['Material']}.jpg" in available_specs or f"{item['Material']}.png" in available_specs:
                    has_image = "SI"

            # Construct readable line with FICHA tag, IMG tag and TIP
            ficha_tag = "SI" if match else "NO"
            
            try:
                raw_price = item.get('Precio Contado', 0)
                precio = f"${float(raw_price):,.0f}" if pd.notnull(raw_price) and str(raw_price).replace('.','',1).isdigit() else str(raw_price)
            except:
                precio = str(item.get('Precio Contado', '-'))

            specs = item.get('especificaciones', '-')
            
            # Use expert tip if available, fallback to inventory tip
            sku_str = str(item['Material'])
            final_tip = expert_tips.get(sku_str, item.get('tip_venta', '-'))
            if not final_tip or final_tip == "nan" or pd.isna(final_tip): final_tip = "-"

            try:
                stock_val = int(float(item.get('CantDisponible', 0)))
            except:
                stock_val = 0

            line = f"- [ID: {item['Material']}] MODELO: {item['Subproducto']} | FICHA: {ficha_tag} | IMG: {has_image} | CATEGORIA: {item['categoria']} | MARCA: {item['marca']} | DESC: {specs} | STOCK: {stock_val} | PRECIO CONTADO: {precio} | TIP: {final_tip}\n"
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
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"DEBUG RESPONSE: {response_text[:300]}...\n")
            return {"response": response_text}
        else:
            response = model.generate_content(full_prompt)
            response_text = response.text.strip()
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"DEBUG RESPONSE (FALLBACK): {response_text[:300]}...\n")
            return {"response": response_text}
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
