import json
import os

STORAGE_DIR = "backend/storage"
INVENTORY_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
MAPPING_FILE = os.path.join(STORAGE_DIR, "quota_mapping.json")

def find_missing_quotas():
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    
    missing = []
    for item in inventory:
        mat = str(item["Material"]).strip()
        if mat not in mapping:
            missing.append({
                "Material": mat,
                "Subproducto": item["Subproducto"]
            })
            
    print(f"Total inventory items: {len(inventory)}")
    print(f"Items missing quotas: {len(missing)}")
    if missing:
        print("\nFirst 10 missing items:")
        for m in missing[:10]:
            print(f" - {m['Material']}: {m['Subproducto']}")

if __name__ == "__main__":
    find_missing_quotas()
