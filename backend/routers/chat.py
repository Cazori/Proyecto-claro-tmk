import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from config import CLEO_PROMPT, SYNONYMS
from utils import log_debug
from services.ai_service import ai_service
from services.inventory_service import inventory_service

router = APIRouter()

@router.get("/api/pool-stats")
async def get_pool_stats():
    """Get AI pool performance statistics"""
    from config import get_ai_pool
    pool = get_ai_pool()
    if pool:
        return pool.get_stats()
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
            
        # Generic plural removal
        k_norm = k.rstrip('s') if k.endswith('s') and len(k) >= 3 else k
        # Apply mapping (laptop->prt, hp->hewp)
        k_norm = SYNONYMS.get(k_norm, SYNONYMS.get(k, k_norm))
        
        if len(k_norm) >= 2 or k_norm.isdigit() or '"' in k_norm or k_norm in ["tv", "sw", "bt", "tab", "ptn"]:
            valid_keywords.append(k_norm)
    
    if "tv" in valid_keywords:
        for i, k in enumerate(valid_keywords):
            if k.isdigit() and '\"' not in k:
                valid_keywords[i] = k + '\"'
    
    log_debug(f"Keywords procesadas: {valid_keywords}")
    
    results = pd.DataFrame()
    fast_path_used = False
    
    # 1. Fast Path: Keyword matching
    if valid_keywords:
        direct_matches = inventory_service.filter_inventory(df, valid_keywords)
        if 0 < len(direct_matches) < 100:
            log_debug(f"FAST PATH: {len(direct_matches)} coincidencias directas.")
            results = direct_matches
            fast_path_used = True

    # 2. AI Path: Intent analysis
    if not fast_path_used:
        log_debug("AI PATH: Analizando intención de búsqueda...")
        intent = await ai_service.analyze_intent(query)
        log_debug(f"Intención: {intent}")
        results = inventory_service.apply_intent_filters(df, intent)
        log_debug(f"AI PATH: {len(results)} resultados encontrados.")

        # Fallback if AI filtering fails but we have keywords
        if results.empty and valid_keywords:
            log_debug("AI PATH VACÍO: Aplicando fallback a palabras clave.")
            results = inventory_service.filter_inventory(df, valid_keywords)
            log_debug(f"Fallback: {len(results)} resultados.")

    # 3. Format context and generate response
    inventory_context = inventory_service.format_inventory_context(results)
    
    # Restore the v1.9.0 recommendation rule
    full_prompt = f"""
    {CLEO_PROMPT}

    DATOS DEL INVENTARIO ENCONTRADO:
    {inventory_context}

    PREGUNTA DEL USUARIO:
    "{query}"
    
    REGLA: Si no hay inventario, sugiere productos similares si los ves, o di que no hay stock disponible.
    """

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
