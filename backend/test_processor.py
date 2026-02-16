from processor import get_latest_inventory

print("Testing get_latest_inventory() with new regex logic...")
df = get_latest_inventory()

if df is not None:
    print(f"SUCCESS! Found {len(df)} rows.")
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head())
else:
    print("FAILURE: Still getting None.")
