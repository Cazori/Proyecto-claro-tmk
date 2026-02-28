import os
import re
import json
from datetime import datetime
from config import SPECS_DIR, NOISE_WORDS, SPECS_MAPPING_FILE
from embeddings_service import embeddings_service

# In-request cache for spec resolution to avoid redundant calls
_spec_match_cache = {}

def clear_spec_cache():
    """Clear the in-memory spec resolution cache."""
    global _spec_match_cache
    _spec_match_cache = {}

def log_debug(msg):
    """Log debug information to a local file"""
    try:
        with open("chat_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
    except:
        pass

def normalize_str(s):
    """Basic string normalization for comparisons"""
    return str(s).lower().strip() if s else ""

def check_variant_mismatch(p_name, f_name):
    """Smart check to prevent matching between different variants (e.g. Pro vs Ultra)"""
    p_norm = p_name.upper().replace("TELEVISOR", "TV").replace("TABLET", "TAB").replace("CELULAR", "CEL")
    f_norm = f_name.upper().replace("TELEVISOR", "TV").replace("TABLET", "TAB").replace("CELULAR", "CEL")
    
    p_clean_str = re.sub(r'[^A-Z0-9\s]', ' ', p_norm)
    f_clean_str = re.sub(r'[^A-Z0-9\s]', ' ', f_norm)
    
    p_words = set(p_clean_str.split())
    f_words = set(f_clean_str.split())
    
    # Critical Version Keywords (Hard mismatch)
    versions = ["PRO", "ULTRA", "MAX", "PLUS", "LITE", "5G", "MINI"]
    for v in versions:
        in_p = v in p_words
        in_f = v in f_words or any(v in word for word in f_words)
        if in_p != in_f:
            return True
            
    # Category Check (Soft mismatch)
    categories = ["TV", "TAB", "CEL"]
    p_cat = next((c for c in categories if c in p_words), None)
    f_cat = next((c for c in categories if c in f_words), None)
    if p_cat and f_cat and p_cat != f_cat:
        return True
            
    # Smart Numeric Check
    f_sig_nums = {n for n in re.findall(r'\d+', f_clean_str) if len(n) >= 2}
    p_nums_all = set(re.findall(r'\d+', p_clean_str))
    if f_sig_nums and not f_sig_nums.intersection(p_nums_all):
        return True
            
    return False

def resolve_spec_match(mat_id, subprod, available_specs, manual_map):
    """Hybrid logic to match inventory item with a technical sheet file."""
    subprod_upper = str(subprod).upper()
    mat_id_str = str(mat_id)

    # Check cache first
    cache_key = f"{mat_id_str}:{subprod_upper}"
    if cache_key in _spec_match_cache:
        return _spec_match_cache[cache_key]

    # 1. Manual Mapping (Priority 1: Exact ID)
    if mat_id_str in manual_map:
        val = manual_map[mat_id_str]
        if isinstance(val, dict):
            for size_key, fname in val.items():
                if size_key in subprod_upper:
                    _spec_match_cache[cache_key] = fname
                    return fname
        else:
            _spec_match_cache[cache_key] = val
            return val

    # 1b. Manual Mapping (Priority 2: Substring)
    for key, val in manual_map.items():
        if key.upper() in subprod_upper:
            if isinstance(val, dict):
                for size_key, fname in val.items():
                    if size_key in subprod_upper:
                        _spec_match_cache[cache_key] = fname
                        return fname
                continue 
            _spec_match_cache[cache_key] = val
            return val
            
    # 2. Exact Material ID Match (Priority 3)
    if len(mat_id_str) >= 4:
        for f in available_specs:
            if re.search(rf"\b{mat_id_str}\b", f):
                _spec_match_cache[cache_key] = f
                return f
            
    # 3. Robust Keyword Scoring (Priority 3)
    clean_p_name = re.sub(r'[^A-Z0-9\s]', ' ', subprod_upper)
    p_words = [w for w in clean_p_name.lower().split() if (len(w) > 2 or w.isdigit()) and w not in NOISE_WORDS]
    
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
    semantic_match = embeddings_service.find_best_match(subprod_upper, available_specs, threshold=0.82)
    if semantic_match:
        if not check_variant_mismatch(subprod_upper, semantic_match):
            _spec_match_cache[cache_key] = semantic_match
            return semantic_match
    
    _spec_match_cache[cache_key] = None
    return None
