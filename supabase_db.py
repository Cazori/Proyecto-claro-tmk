import pandas as pd

async def save_inventory_to_db(df):
    """Placeholder that pretends to save inventory to Supabase.
    Currently does nothing but prints a message for debugging."""
    print("[supabase_db] save_inventory_to_db called – no operation performed.")
    return None

async def get_inventory_from_db(columns="*"):
    """Return an empty DataFrame as a placeholder for Supabase data retrieval."""
    print("[supabase_db] get_inventory_from_db called – returning empty DataFrame.")
    return pd.DataFrame()

async def get_metadata_db():
    """Return None to indicate no metadata available in this stub."""
    print("[supabase_db] get_metadata_db called – returning None.")
    return None
