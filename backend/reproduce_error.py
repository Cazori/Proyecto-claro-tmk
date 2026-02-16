import re
import json
import os
import pandas as pd

# Mocking the environment for the reproduction test
KNOWLEDGE_FILE = "expert_knowledge.json"
STORAGE_DIR = "storage"
SYNONYMS = {
    "port": "portatil", "portatil": "prt", "portatiles": "prt", "laptop": "prt", "laptops": "prt",
    "hp": "hewp", "hewlett": "hewp", "packard": "hewp", "ng": "negro", "ngr": "negro",
    "bl": "blanco", "blnc": "blanco", "cel": "celular", "celulares": "celular",
    "tel": "telefono", "telefonos": "celular", "aud": "audifonos", "audifono": "audifonos",
    "smrt": "smart", "watch": "reloj", "sw": "reloj", "tablet": "tab", "tablets": "tab",
}

def reproduce(query):
    print(f"\nQUERY: {query}")
    clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
    words = clean_query.split()
    noise_words = {"que", "tenemos", "hay", "donde", "como", "cual", "cuales", "los", "las", "un", "una", 
                   "el", "la", "en", "con", "por", "de", "para", "mi", "mis", "tu", "tus", "su", "sus", 
                   "hola", "cleo", "pues", "ps", "dame", "busca", "encuentra", "tienes", "ver", "dime", "podrias",
                   "manejamos", "venden", "vendes", "disponibles", "inventario", "lista", "muéstrame", "mira", "qué", "sobre"}
    raw_keywords = [w for w in words if w not in noise_words and len(w) > 1]
    
    if not raw_keywords:
        categories = {"portatiles": "prt", "laptops": "prt", "televisores": "tv", "celulares": "celular", "tablets": "tab"}
        found_cat = [v for k,v in categories.items() if k in words]
        if found_cat:
            raw_keywords = [found_cat[0]]
        else:
            print("No keywords found.")
            return

    def calculate_score(product_name):
        name_lower = product_name.lower()
        score = 0
        all_req_match = True
        for raw_kw in raw_keywords:
            syn = SYNONYMS.get(raw_kw, raw_kw)
            if raw_kw in name_lower or (syn != raw_kw and syn in name_lower):
                score += (len(raw_kw) * 20)
            else:
                all_req_match = False
        if all_req_match and raw_keywords:
            score += 2000
        return score

    print(f"Keywords: {raw_keywords}")
    # Simulate dataframe check if possible
    # (Assuming we skip DF for now and just check logic flow)
    print("Logic flow reached end of RAG assembly.")

reproduce("Que portatiles tenemos?")
reproduce("Que tablets manejamos?")
reproduce("tenemos tablets samsung?")
