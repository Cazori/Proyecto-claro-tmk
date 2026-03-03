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
    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle new format {last_update, records} or legacy list
        inventory_items = data.get("records", data) if isinstance(data, dict) else data
        
        active_materials = {str(item["Material"]).split('.')[0].strip() for item in inventory_items if "Material" in item}
        print(f"📦 Inventario cargado: {len(active_materials)} materiales activos.")

        if not os.path.exists(QUOTAS_EXCEL):
            raise FileNotFoundError(f"No se encontró el archivo de cuotas en {QUOTAS_EXCEL}")

        # 1. Load the Excel file to inspect sheets
        xl = pd.ExcelFile(QUOTAS_EXCEL)
        sheet_names = xl.sheet_names
        print(f"📄 Hojas encontradas en el Excel: {sheet_names}")
        
        df = None
        target_sheet = None
        header_row_idx = None
        
        # 2. Iterate through sheets to find the one with 'Material'
        for sheet in sheet_names:
            temp_df = pd.read_excel(QUOTAS_EXCEL, sheet_name=sheet, header=None).head(30)
            for i, row in temp_df.iterrows():
                if "Material" in [str(v).strip() for v in row.values if pd.notna(v)]:
                    target_sheet = sheet
                    header_row_idx = i
                    print(f"🎯 Hoja detectada: '{target_sheet}' (Encabezados en fila {header_row_idx})")
                    break
            if target_sheet: break
            
        if not target_sheet:
            raise ValueError("No se encontró ninguna hoja con la columna 'Material'.")

        # 3. Load full target sheet
        df = pd.read_excel(QUOTAS_EXCEL, sheet_name=target_sheet, header=header_row_idx)
        
        # Cleanup column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find critical columns
        column_map = {}
        for col in df.columns:
            str_col = str(col).lower()
            if "mes" not in str_col: continue
            if "36" in str_col: column_map["36"] = col
            elif "24" in str_col: column_map["24"] = col
            elif "18" in str_col: column_map["18"] = col
            elif "12" in str_col: column_map["12"] = col
            elif "6" in str_col and "36" not in str_col: column_map["6"] = col

        print(f"🔍 Columnas de cuotas detectadas: {column_map}")
        if not column_map:
            print("⚠️ No se detectaron columnas de meses.")

        final_mapping = {}
        matched_count = 0

        for _, row in df.iterrows():
            if "Material" not in row or pd.isna(row["Material"]): continue
            raw_mat = str(row["Material"]).split('.')[0].strip()
            
            plans = {}
            for months, real_col in column_map.items():
                val = row[real_col]
                if pd.notna(val) and val != "No Aplica":
                    try:
                        if isinstance(val, str):
                            val = val.replace("$", "").replace(",", "").strip()
                        plans[months] = int(float(val))
                    except: continue
            
            if plans:
                final_mapping[raw_mat] = plans
                matched_count += 1

        # 4. Save results
        with open(OUTPUT_MAPPING, "w", encoding="utf-8") as f:
            json.dump(final_mapping, f, indent=2)

        print(f"✅ Proceso completado. Se mapearon cuotas para {matched_count} equipos.")
        del df
        gc.collect()

    except Exception as e:
        print(f"❌ Error procesando Excel: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    process_quotas()
