import os
import json
import re
import pdfplumber

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPECS_DIR = os.path.join(BASE_DIR, "specs")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "expert_knowledge.json")

def extract_from_pdf(file_path):
    """Simple extractor for text-based PDFs"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Look for SKU pattern: XXXXXXX#XXX or similar
        sku_match = re.search(r"([A-Z0-9]{7,}(?:#[A-Z0-9]{3})?)", text)
        sku = sku_match.group(1) if sku_match else "Desconocido"
        
        # Very basic heuristics for model and specs
        lines = text.split("\n")
        model = lines[0].strip() if lines else "Modelo Desconocido"
        specs = " ".join(lines[1:5]).strip()
        
        return {"sku": sku, "model": model, "specs": specs}
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return None

def rebuild_knowledge():
    """Scans the specs folder and rebuilds the JSON index"""
    if not os.path.exists(SPECS_DIR):
        return
        
    knowledge = []
    # Load existing to avoid losing manual edits if we add a 'manual' flag
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            knowledge = json.load(f)

    existing_skus = {item.get("sku") for item in knowledge}
    
    files = os.listdir(SPECS_DIR)
    for filename in files:
        file_path = os.path.join(SPECS_DIR, filename)
        if filename.lower().endswith(".pdf"):
            # Try extraction
            data = extract_from_pdf(file_path)
            if data and data["sku"] not in existing_skus:
                knowledge.append(data)
                existing_skus.add(data["sku"])
        # For images, we'll need either OCR or manual assistance
        # For now, we just log them
        elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
             print(f"Imagen detectada: {filename}. Pendiente de OCR o revisión manual.")

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=4)
    
    print(f"Memoria Maestra sincronizada. Total items: {len(knowledge)}")

if __name__ == "__main__":
    rebuild_knowledge()
