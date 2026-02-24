import pandas as pd
import json
import os

STORAGE_DIR = "backend/storage"
INVENTORY_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
QUOTAS_EXCEL = os.path.join(STORAGE_DIR, "cuotas.xlsx")

def debug_quotas():
    if not os.path.exists(INVENTORY_FILE):
        print("No inventory file found.")
        return
    
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)
    
    inventory_mats = {str(item["Material"]).strip() for item in inventory}
    print(f"Total active materials in inventory: {len(inventory_mats)}")
    
    if not os.path.exists(QUOTAS_EXCEL):
        print("No quotas excel found.")
        return

    try:
        df = pd.read_excel(QUOTAS_EXCEL, sheet_name='Lista', header=None)
        
        # Find header row
        header_row_idx = None
        for i, row in df.iterrows():
            if "Material" in str(row.values):
                header_row_idx = i
                break
        
        if header_row_idx is None:
            print("Header 'Material' not found in Excel.")
            return
            
        df.columns = df.iloc[header_row_idx]
        df = df.iloc[header_row_idx + 1:]
        
        target_mat = "7023128"
        print(f"\nChecking for Material {target_mat} in Excel...")
        
        # Found rows with target_mat
        matches = []
        for _, row in df.iterrows():
            mat_val = str(row["Material"]).split('.')[0].strip()
            if mat_val == target_mat:
                matches.append(row.to_dict())
        
        if matches:
            print(f"✅ Found {len(matches)} occurrences of {target_mat} in Excel.")
            for m in matches:
                # Check if it has quota values
                quotas = {k: v for k, v in m.items() if "Mes" in str(k)}
                print(f"  Row Data (Quotas): {quotas}")
        else:
            print(f"❌ Material {target_mat} NOT found in Excel (using .split('.')[0].strip()).")
            # Show some raw values around that range
            print("\nSample Material values from Excel:")
            print(df["Material"].astype(str).unique()[:20])

        print(f"\nIs {target_mat} in inventory? {'YES' if target_mat in inventory_mats else 'NO'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_quotas()
