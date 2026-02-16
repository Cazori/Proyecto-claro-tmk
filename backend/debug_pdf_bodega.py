
import pdfplumber
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
if not files:
    print("No PDFs found")
else:
    latest_file = max(files, key=os.path.getmtime)
    print(f"Analyzing: {latest_file}")
    
    with pdfplumber.open(latest_file) as pdf:
        for i, page in enumerate(pdf.pages[:3]):
            text = page.extract_text()
            if not text: continue
            clean_text = text.replace('\n', ' ')
            
            # Bodega Pattern
            bodega_match = re.search(r"CEM\s+([\w\s-]+?)(?:\s+[CH]\d{3}|\d{7})", clean_text)
            page_bodega = bodega_match.group(1).strip() if bodega_match else "Desconocida"
            
            print(f"Page {i+1} Bodega extracted: '{page_bodega}'")
            print(f"Match BOGOT (upper): {'BOGOT' in page_bodega.upper()}")
