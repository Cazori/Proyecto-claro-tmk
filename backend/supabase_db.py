import os
import json
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key) if url and key else None

# --- DATABASE LOGIC ---

async def save_inventory_to_db(df: pd.DataFrame):
    if supabase is None: return
    
    # 1. Convert DataFrame to records
    records = df.to_dict('records')
    
    # 2. Clear previous inventory (optional, or version it)
    # For now, we simple-replace for the 'Cleo' experience
    try:
        supabase.table('inventory').delete().neq('Material', '0').execute()
        
        # 3. Batch insert (Supabase handles large inserts well)
        # We split in chunks just in case
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            supabase.table('inventory').insert(chunk).execute()
            
        # 4. Update metadata
        await update_metadata_db()
        print(f"✓ {len(records)} productos guardados en Supabase.")
    except Exception as e:
        print(f"✗ Error guardando en Supabase: {e}")

async def get_inventory_from_db():
    if supabase is None: return None
    try:
        response = supabase.table('inventory').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"✗ Error leyendo de Supabase: {e}")
    return None

async def update_metadata_db():
    if supabase is None: return
    now = datetime.now().isoformat()
    try:
        supabase.table('metadata').upsert({"id": 1, "last_update": now, "status": "ready"}).execute()
    except Exception as e:
        print(f"✗ Error actualizando metadata: {e}")

async def get_metadata_db():
    if supabase is None: return None
    try:
        response = supabase.table('metadata').select("*").eq("id", 1).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"✗ Error obteniendo metadata: {e}")
    return None

# --- STORAGE LOGIC (SPECS) ---

async def upload_spec_to_supabase(file_path: str, filename: str):
    if supabase is None: return
    try:
        with open(file_path, 'rb') as f:
            # Upsert = True to overwrite if same name
            supabase.storage.from_('specs').upload(
                path=filename,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        print(f"✓ Ficha {filename} subida a Supabase Storage.")
    except Exception as e:
        print(f"✗ Error subiendo ficha a Storage: {e}")

def get_spec_url_supabase(filename: str):
    if supabase is None: return None
    # Public URL if bucket is public
    return supabase.storage.from_('specs').get_public_url(filename)

async def list_specs_supabase():
    if supabase is None: return []
    try:
        response = supabase.storage.from_('specs').list()
        return [f['name'] for f in response]
    except Exception as e:
        print(f"✗ Error listando fichas: {e}")
        return []
