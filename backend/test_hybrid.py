from processor import get_latest_inventory
import pandas as pd
import os

def test_hybrid_extraction():
    print("Testing Hybrid Extraction...")
    import os
    from processor import STORAGE_DIR, PROCESSED_DATA_FILE
    print(f"STORAGE_DIR: {os.path.abspath(STORAGE_DIR)}")
    print(f"PROCESSED_FILE: {os.path.abspath(PROCESSED_DATA_FILE)}")
    
    df = get_latest_inventory()
    if df is not None:
        print(f"Extracted {len(df)} rows.")
        print("\nColumns found:", df.columns.tolist())
        print("\nFirst 5 rows (Normalized):")
        print(df[["Subproducto", "categoria", "marca", "modelo_limpio", "CantDisponible"]].head())
        
        # Verify specific categories
        tvs = df[df["categoria"].str.contains("TV", case=False, na=False)]
        print(f"\nTVs found: {len(tvs)}")
        
        patinetas = df[df["categoria"].str.contains("Patineta", case=False, na=False)]
        print(f"Patinetas found: {len(patinetas)}")
    else:
        print("No inventory data found.")

if __name__ == "__main__":
    test_hybrid_extraction()
