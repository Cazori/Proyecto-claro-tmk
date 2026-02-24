from supabase_db import supabase
import json

def discover_columns():
    test_records = [
        {"Material": "7020000", "Subproducto": "TEST", "CantDisponible": 1},
        {"Material": "7020001", "Subproducto": "TEST", "Cant_Disponible": 1},
        {"Material": "7020002", "Subproducto": "TEST", "stock": 1},
        {"Material": "7020003", "Subproducto": "TEST", "cantidad": 1},
        {"Material": "7020004", "Subproducto": "TEST", "Cant Disponible": 1},
        {"Material": "7020005", "Subproducto": "TEST", "stock_disponible": 1},
    ]
    
    for rec in test_records:
        try:
            print(f"Trying keys: {list(rec.keys())}")
            supabase.table('inventory').insert(rec).execute()
            print("  ✅ Success!")
            # Clean up
            supabase.table('inventory').delete().eq(list(rec.keys())[0], "7020000").execute()
            return list(rec.keys())
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    return None

if __name__ == "__main__":
    discover_columns()
