import os
import json
import asyncio
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from config import STORAGE_DIR, SPECS_DIR, SPECS_MAPPING_FILE
from processor import get_latest_inventory
from utils import resolve_spec_match
from supabase_db import get_spec_url_supabase, list_specs_supabase, upload_spec_to_supabase

router = APIRouter()
_mapping_lock = asyncio.Lock()

@router.get("/specs/{filename}")
async def get_spec_image(filename: str):
    local_path = os.path.join(SPECS_DIR, filename)
    if os.path.exists(local_path):
        return FileResponse(local_path)
    
    # Try cloud
    cloud_url = get_spec_url_supabase(filename)
    if cloud_url:
        return RedirectResponse(cloud_url)
    
    raise HTTPException(status_code=404, detail="Imagen no encontrada local ni en la nube.")

@router.get("/specs-list")
async def list_specs():
    """List all available technical sheet images (Local + Cloud)"""
    local_files = []
    if os.path.exists(SPECS_DIR):
        local_files = [f for f in os.listdir(SPECS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
    
    try:
        cloud_files = await list_specs_supabase()
    except:
        cloud_files = []
        
    return list(set(local_files + cloud_files))

@router.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Formato no soportado.")
    
    file_path = os.path.join(SPECS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Cloud Storage Upload in background
    asyncio.create_task(upload_spec_to_supabase(file_path, file.filename))
    
    return {"message": "Ficha técnica recibida y sincronizada con la nube."}

@router.get("/specs-mapping")
async def get_specs_mapping():
    """Endpoint for frontend to get the resolved MaterialID -> Filename map."""
    df = await get_latest_inventory()
    if df is None: return {}
    
    cache_file = os.path.join(STORAGE_DIR, "specs_resolved_cache.json")
    inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
    
    # 1. Try persistent disk cache first (fastest) - OUTSIDE LOCK
    if os.path.exists(cache_file) and os.path.exists(inv_file):
        try:
            if os.path.getmtime(cache_file) >= os.path.getmtime(inv_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Cache read error: {e}")

    # 2. Re-calculate if cache is stale or missing - INSIDE LOCK
    async with _mapping_lock:
        # Re-check cache in case someone else just filled it
        if os.path.exists(cache_file) and os.path.getmtime(cache_file) >= os.path.getmtime(inv_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        print("Recalculando mapeo de imágenes (Caché vencido)...")
    try:
        available_specs = os.listdir(SPECS_DIR) if os.path.exists(SPECS_DIR) else []
        manual_map = {}
        if os.path.exists(SPECS_MAPPING_FILE):
            with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
                manual_map = json.load(f)
    except Exception as e:
        print(f"Error loading mapping files: {e}")
        available_specs, manual_map = [], {}

    resolved = {}
    for _, item in df.iterrows():
        material_str = str(item['Material'])
        match = resolve_spec_match(material_str, item['Subproducto'], available_specs, manual_map)
        if match:
            resolved[material_str] = match
            
    # Save cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(resolved, f, indent=4)
    except Exception as e:
        print(f"Cache write error: {e}")

    return resolved
