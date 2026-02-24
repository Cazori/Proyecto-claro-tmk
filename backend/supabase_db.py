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
    
    # 1. Prepare safe records (only send columns that exist in the remote schema)
    # Based on discovery, remote only has: Material, Subproducto, categoria, marca, modelo_limpio, especificaciones
    verified_cols = ['Material', 'Subproducto', 'categoria', 'marca', 'modelo_limpio', 'especificaciones']
    
    safe_df = df.copy()
    available_cols = [c for c in verified_cols if c in safe_df.columns]
    safe_df = safe_df[available_cols]
    
    records = safe_df.to_dict('records')
    
    # 2. Clear previous inventory
    try:
        supabase.table('inventory').delete().neq('Material', '0').execute()
        
        # 3. Batch insert
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            supabase.table('inventory').insert(chunk).execute()
            
        # 4. Update metadata
        await update_metadata_db()
        print(f"✓ {len(records)} productos persistidos en Supabase DB.")
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

async def save_quotas_to_db(mapping: dict):
    if supabase is None: return
    try:
        # We store the quota mapping as a single JSON object in a dedicated table 'quotas'
        # with id=1 for simplicity (or we could store it as records per SKU)
        # Let's use a simple key-value approach for the whole JSON for speed
        payload = {"id": 1, "data": mapping, "updated_at": datetime.now().isoformat()}
        supabase.table('quotas').upsert(payload).execute()
        print(f"✓ Mapeo de cuotas ({len(mapping)} equipos) guardado en Supabase.")
    except Exception as e:
        print(f"✗ Error guardando cuotas en Supabase: {e}")

async def get_quotas_from_db():
    if supabase is None: return None
    try:
        response = supabase.table('quotas').select("data").eq("id", 1).execute()
        if response.data:
            return response.data[0]["data"]
    except Exception as e:
        print(f"✗ Error leyendo cuotas de Supabase: {e}")
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

# --- STORAGE LOGIC (INVENTORY PDF) ---

async def upload_inventory_pdf_to_supabase(file_path: str, filename: str):
    if supabase is None: return
    try:
        with open(file_path, 'rb') as f:
            supabase.storage.from_('inventories').upload(
                path=filename,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        print(f"✓ PDF {filename} subido a Supabase Storage.")
    except Exception as e:
        print(f"✗ Error subiendo PDF a Storage: {e}")

async def download_latest_inventory_pdf_from_supabase(local_dir: str):
    if supabase is None: return None
    try:
        # Get list of files in 'inventories' bucket
        files = supabase.storage.from_('inventories').list()
        if not files: return None
        
        # Sort by creation date (if metadata available) or just take one for now
        # Actually Supabase list() returns metadata. Sort by 'created_at'.
        files.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        latest_filename = files[0]['name']
        
        local_path = os.path.join(local_dir, latest_filename)
        with open(local_path, 'wb') as f:
            res = supabase.storage.from_('inventories').download(latest_filename)
            f.write(res)
        
        print(f"✓ PDF {latest_filename} descargado de Supabase Storage.")
        return local_path
    except Exception as e:
        print(f"✗ Error descargando PDF de Supabase: {e}")
        return None
