from supabase_db import supabase
import pandas as pd
import os
import json

def exhaustive_discovery():
    df = pd.read_json("storage/processed_inventory.json")
    columns = list(df.columns)
    print(f"Testing columns from DF: {columns}")
    
    mat = "7029999"
    # Basic record
    base = {"Material": mat, "Subproducto": "DISCOVERY_TEST"}
    
    found = []
    for col in columns:
        if col in ["Material", "Subproducto"]: continue
        try:
            record = base.copy()
            record[col] = 0 # Try with 0
            supabase.table('inventory').insert(record).execute()
            print(f"  ✅ Column '{col}' EXISTS")
            found.append(col)
            # Cleanup
            supabase.table('inventory').delete().eq("Material", mat).execute()
        except Exception as e:
            # print(f"  ❌ Column '{col}' NOT FOUND: {e}")
            pass
            
    print(f"\nFinal discovered schema: {['Material', 'Subproducto'] + found}")

if __name__ == "__main__":
    exhaustive_discovery()
