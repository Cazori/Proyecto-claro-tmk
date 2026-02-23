import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from config import CLEO_PROMPT
from utils import log_debug
from services.ai_service import ai_service
from services.inventory_service import inventory_service

router = APIRouter()

# Synonym/code mapping: user terms → internal inventory codes
# CRITICAL: Must match the normalized codes used in the processed inventory
SYNONYMS = {
    "port": "portatil", "portatil": "prt", "portatiles": "prt", "laptop": "prt", "laptops": "prt",
    "hp": "hewp", "hewlett": "hewp", "packard": "hewp", "ng": "negro", "ngr": "negro",
    "bl": "blanco", "blnc": "blanco", "cel": "celular", "celulares": "celular",
    "tel": "telefono", "telefonos": "celular", "aud": "audifonos", "audifono": "audifonos",
    "smrt": "smart", "watch": "reloj", "sw": "reloj",
    "ryzen": "rzn", "intel": "ic", "core": "ic", "ram": "g", "gb": "g"
}

@router.get("/api/pool-stats")
async def get_pool_stats():
    """Get AI pool performance statistics"""
    from config import ai_pool
    if ai_pool:
        return ai_pool.get_stats()
    return {"error": "AI Pool not initialized", "fallback_mode": "single_gemini_model"}

@router.post("/generate-tip")
async def generate_tip(data: dict):
    model_name = data.get("model")
    specs = data.get("specs")
    if not model_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del modelo.")
    
    tip = await ai_service.generate_sales_tip(model_name, specs)
    return {"tip": tip}

@router.get("/chat")
async def chat(query: str):
    df = await inventory_service.get_latest_inventory_df()
    if df is None:
        return {"response": "Sube un inventario PDF para comenzar."}

    log_debug(f"QUERY RECIBIDA (Original): {query}")
        
    # Basic cleaning and keyword extraction for fast path
    query_clean = query.lower().replace(" pulgadas", "\"").replace(" pulgada", "\"").replace(" pulgs", "\"")
    query_clean = query_clean.replace("pulgadas", "\"").replace("pulgada", "\"").replace("pulgs", "\"")
    query_clean = query_clean.replace("ram", "g").replace("gb", "g")
    
    raw_keywords = query_clean.split()
    stop_words = ["de", "con", "el", "la", "los", "las", "un", "una", "en", "para", "por"]
    
    valid_keywords = []
    for k in raw_keywords:
        if k in stop_words or k == "\"": continue
        if k in ["televisor", "televisores", "television", "televisiones"]: 
            valid_keywords.append("tv")
            continue
        if k in ["tablet", "tablets", "tableta", "tabletas"]: 
            valid_keywords.append("tab")
            continue
        if k in ["patineta", "patinetas", "scooter", "scooters"]: 
            valid_keywords.append("ptn")
            continue
            
        k_norm = k.rstrip('s') if k.endswith('s') and len(k) >= 3 else k
        # Apply synonym mapping (laptop→prt, hp→hewp, etc.)
        k_norm = SYNONYMS.get(k_norm, SYNONYMS.get(k, k_norm))
        if len(k_norm) >= 2 or k_norm.isdigit() or '"' in k_norm or k_norm in ["tv", "sw", "bt", "tab", "ptn"]:
            valid_keywords.append(k_norm)
    
    if "tv" in valid_keywords:
        for i, k in enumerate(valid_keywords):
            if k.isdigit() and '\"' not in k:
                valid_keywords[i] = k + '\"'
    
    log_debug(f"Keywords válidas final: {valid_keywords}")
    
    results = pd.DataFrame()
    fast_path_used = False
    
    # 1. Fast Path: Keyword matching
    if valid_keywords:
        direct_matches = inventory_service.filter_inventory(df, valid_keywords)
        if 0 < len(direct_matches) < 100:
            results = direct_matches
            fast_path_used = True

    # 2. AI Path: Intent analysis
    if not fast_path_used:
        intent = await ai_service.analyze_intent(query)
        results = inventory_service.apply_intent_filters(df, intent)

        # Fallback if AI filtering fails but we have keywords
        if results.empty and valid_keywords:
            results = inventory_service.filter_inventory(df, valid_keywords)

    # 3. Format context and generate response
    inventory_context = inventory_service.format_inventory_context(results)
    full_prompt = f"{CLEO_PROMPT}\n\nDATOS DEL INVENTARIO ENCONTRADO:\n{inventory_context}\n\nPREGUNTA DEL USUARIO: \"{query}\"\n"

    try:
        response_text = await ai_service.generate_response(full_prompt)
        if not response_text:
             return {"response": "Lo siento, el sistema de IA no está disponible."}
        return {"response": response_text}
    except Exception as e:
        print(f"Error Cleo: {e}")
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return {"response": "Cleo ha alcanzado el límite de consultas. Por favor, espera unos minutos o añade más APIs."}
        return {"response": "Lo siento, tuve un problema analizando el inventario."}
