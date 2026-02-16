import pdfplumber
import os
import re

file_path = r"c:\Users\Usuario\Desktop\Kaz\Programacion\Proyecto Claro tmk\backend\storage\Inventario 06-02-26 C230.pdf"

try:
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
        
        lines = full_text.split("\n")
        print(f"Total lines extracted: {len(lines)}")
        
        # Look for the start of the data
        # Pattern: Bodega (text) + Centro (Cxxx) + Almacen (Hxxx) + Material (7xxxxxx)
        # Example: CEM Bogotá - ZF C230 H001 7023240 SMRTWTCH...
        
        pattern = r"^(CEM\s.*?)\s+(C\d{3})\s+(H\d{3})\s+(\d{7})(.*?)$"
        
        data = []
        for line in lines:
            match = re.search(pattern, line)
            if match:
                bodega = match.group(1).strip()
                centro = match.group(2).strip()
                almacen = match.group(3).strip()
                material = match.group(4).strip()
                rest = match.group(5).strip()
                
                # 'rest' might contain Subproducto and quantities/prices
                # Let's see what's in 'rest'
                data.append({
                    "Bodega": bodega,
                    "Material": material,
                    "Resto": rest
                })
        
        print(f"Found {len(data)} potential rows using pattern")
        if data:
            for i in range(min(5, len(data))):
                print(f"Row {i+1}: {data[i]}")

except Exception as e:
    print(f"Error: {e}")
