import pandas as pd
import json
import os
import gc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
INVENTORY_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
QUOTAS_EXCEL = os.path.join(STORAGE_DIR, "cuotas.xlsx")
OUTPUT_MAPPING = os.path.join(STORAGE_DIR, "quota_mapping.json")

def process_quotas():
    print("🚀 Iniciando procesamiento de cuotas (Versión Refinada)...")
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)
    
    active_materials = {str(item["Material"]).split('.')[0].strip() for item in inventory}
    print(f"📦 Inventario cargado: {len(active_materials)} materiales activos.")

    # 2. Load Excel without headers first to skip metadata rows
    if not os.path.exists(QUOTAS_EXCEL):
        print(f"❌ Error: No se encontró el archivo de cuotas en {QUOTAS_EXCEL}")
        return

    try:
        # 1. Load the Excel file to inspect sheets
        xl = pd.ExcelFile(QUOTAS_EXCEL)
        sheet_names = xl.sheet_names
        print(f"📄 Hojas encontradas en el Excel: {sheet_names}")
        
        df = None
        target_sheet = None
        header_row_idx = None
        
        # 2. Iterate through sheets to find the one with 'Material'
        for sheet in sheet_names:
            temp_df = pd.read_excel(QUOTAS_EXCEL, sheet_name=sheet, header=None).head(30) # Only check top rows
            for i, row in temp_df.iterrows():
                if "Material" in [str(v).strip() for v in row.values if pd.notna(v)]:
                    target_sheet = sheet
                    header_row_idx = i
                    print(f"🎯 Hoja detectada: '{target_sheet}' (Encabezados en fila {header_row_idx})")
                    break
            if target_sheet: break
            
        if not target_sheet:
            print("❌ No se encontró ninguna hoja con la columna 'Material'.")
            return

        # 3. Load full target sheet
        df = pd.read_excel(QUOTAS_EXCEL, sheet_name=target_sheet, header=header_row_idx)
        
        # Cleanup column names
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
        
        column_map = {}
        for col in df.columns:
            str_col = str(col).lower()
            if "mes" not in str_col:
                continue
                
            if "36" in str_col: column_map["36"] = col
            elif "24" in str_col: column_map["24"] = col
            elif "18" in str_col: column_map["18"] = col
            elif "12" in str_col: column_map["12"] = col
            elif "6" in str_col and "36" not in str_col:
                column_map["6"] = col

        print(f"🔍 Columnas de cuotas detectadas: {column_map}")
        if not column_map:
            print("⚠️ No se detectaron columnas de meses (ej. '6 Meses', '12 Meses'). Verifique el formato.")

        final_mapping = {}
        matched_count = 0

        for _, row in df.iterrows():
            raw_mat = str(row[material_col]).split('.')[0].strip()
            
            # We remove the 'if raw_mat in active_materials' check to be more inclusive
            # and allow the system to have prices ready even for items not currently in stock
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
        
        # Explicit cleanup to save memory on Render
        del df
        gc.collect()

    except Exception as e:
        print(f"❌ Error procesando Excel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_quotas()
