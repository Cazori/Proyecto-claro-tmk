import pandas as pd
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
INVENTORY_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
QUOTAS_EXCEL = os.path.join(STORAGE_DIR, "cuotas.xlsx")
OUTPUT_MAPPING = os.path.join(STORAGE_DIR, "quota_mapping.json")

def process_quotas():
    print("🚀 Iniciando procesamiento de cuotas (Versión Refinada)...")
    
    # 1. Load current inventory
    if not os.path.exists(INVENTORY_FILE):
        print(f"❌ Error: No se encontró el inventario en {INVENTORY_FILE}")
        return
        
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)
    
    active_materials = {str(item["Material"]).split('.')[0].strip() for item in inventory}
    print(f"📦 Inventario cargado: {len(active_materials)} materiales activos.")

    # 2. Load Excel without headers first to skip metadata rows
    if not os.path.exists(QUOTAS_EXCEL):
        print(f"❌ Error: No se encontró el archivo de cuotas en {QUOTAS_EXCEL}")
        return

    try:
        # Load the sheet 'Lista' which seems to be the main one
        sheet_name = 'Lista'
        # Skip the metadata rows (based on inspection, headers are around row 13)
        # We'll load the whole thing and then slice
        df = pd.read_excel(QUOTAS_EXCEL, sheet_name=sheet_name, header=None)
        
        # Based on inspection:
        # Row 13 has the headers
        # Col 4 has 'Material'
        # Col 15 -> 6 meses
        # Col 16 -> 12 meses
        # Col 17 -> 18 meses
        # Col 18 -> 24 meses
        # Col 19 -> 36 meses (approx indices, let's verify)
        
        # We search for the row containing 'Material'
        header_row_idx = None
        for i, row in df.iterrows():
            if "Material" in str(row.values):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            print("❌ No se encontró la fila de encabezados 'Material'.")
            return
            
        print(f"🎯 Encabezados encontrados en fila {header_row_idx}")
        
        # Set headers and slice
        df.columns = df.iloc[header_row_idx]
        df = df.iloc[header_row_idx + 1:]
        
        # Cleanup columns
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find critical columns
        material_col = "Material"
        quota_mapping = {
            "6": "6 Meses",
            "12": "12 Meses",
            "18": "18 Meses",
            "24": "24 Meses",
            "36": "36 Meses"
        }
        
        # Actually in the Excel they might have different names. Let's look for "meses"
        # FIX: Check strictly or ordered to avoid "36" matching "6"
        column_map = {}
        for col in df.columns:
            str_col = str(col).lower()
            if "mes" not in str_col:
                continue
                
            # Check for specific numbers with word boundaries or explicit checks
            # We iterate in reverse order of length/value to avoid subsets? 
            # or just explicit strict checks
            
            if "36" in str_col:
                column_map["36"] = col
            elif "24" in str_col:
                column_map["24"] = col
            elif "18" in str_col:
                column_map["18"] = col
            elif "12" in str_col:
                column_map["12"] = col
            elif "6" in str_col and "36" not in str_col: # Explicitly exclude 36 for 6
                column_map["6"] = col

        print(f"🔍 Columnas detectadas: {column_map}")

        final_mapping = {}
        matched_count = 0

        for _, row in df.iterrows():
            raw_mat = str(row[material_col]).split('.')[0].strip()
            
            if raw_mat in active_materials:
                plans = {}
                for months, real_col in column_map.items():
                    val = row[real_col]
                    if pd.notna(val) and val != "No Aplica":
                        try:
                            # Cleanup currency if it's a string
                            if isinstance(val, str):
                                val = val.replace("$", "").replace(",", "").strip()
                            plans[months] = int(float(val))
                        except:
                            continue
                
                if plans:
                    final_mapping[raw_mat] = plans
                    matched_count += 1

        # 4. Save results
        with open(OUTPUT_MAPPING, "w", encoding="utf-8") as f:
            json.dump(final_mapping, f, indent=2)

        print(f"✅ Proceso completado. Se mapearon cuotas para {matched_count} equipos.")
        print(f"📁 Resultado guardado en {OUTPUT_MAPPING}")

    except Exception as e:
        print(f"❌ Error procesando Excel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_quotas()
