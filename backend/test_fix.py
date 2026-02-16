from processor import get_latest_inventory
import pandas as pd

def test_extraction():
    df = get_latest_inventory()
    if df is None:
        print("Inventory failed to load.")
        return
    
    print(f"Total rows: {len(df)}")
    hp_matches = df[df['Subproducto'].str.contains('HP|HEWP|B8PH', case=False, na=False)]
    
    if hp_matches.empty:
        print("No HP matches found.")
    else:
        print("\n--- HP / HEWP Matches Found ---")
        print(hp_matches[['Subproducto', 'CantDisponible', 'Precio Contado']])

if __name__ == "__main__":
    test_extraction()
