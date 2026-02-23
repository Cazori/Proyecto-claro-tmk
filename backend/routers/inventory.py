import os
import shutil
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from config import STORAGE_DIR
from processor import process_inventory_pdf, rotate_inventories, get_latest_inventory
from supabase_db import upload_inventory_pdf_to_supabase

router = APIRouter()

async def background_inventory_processing(file_path: str, filename: str):
    """Heavy lifting done in the background to avoid HTTP timeouts"""
    try:
        rotate_inventories()
        await process_inventory_pdf(file_path)
        # Cloud Storage Upload (Raw PDF)
        await upload_inventory_pdf_to_supabase(file_path, filename)
        print(f"✓ Inventario {filename} procesado y sincronizado en segundo plano.")
    except Exception as e:
        print(f"✗ ERROR en procesamiento de fondo: {e}")

@router.post("/upload-inventory")
async def upload_inventory(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")
    
    file_path = os.path.join(STORAGE_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add to background tasks
    background_tasks.add_task(background_inventory_processing, file_path, file.filename)
    
    return {
        "message": "Archivo recibido. Cleo está actualizando el inventario en segundo plano. Podrás ver los cambios en unos segundos.",
        "filename": file.filename
    }

@router.get("/inventory-metadata")
async def get_inventory_metadata():
    inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
    if os.path.exists(inv_file):
        last_mod = os.path.getmtime(inv_file)
        dt = datetime.fromtimestamp(last_mod)
        return {"last_update": dt.isoformat(), "status": "active"}
    return {"last_update": None, "status": "no_data"}

@router.get("/find-product")
async def find_product(material: str):
    try:
        df = await get_latest_inventory()
        # Filter by material
        product = df[df['Material'].astype(str) == str(material)]
        if not product.empty:
            item = product.iloc[0].to_dict()
            # Clean for JSON
            cleaned_item = {k: (None if pd.isna(v) else v) for k, v in item.items()}
            return cleaned_item
        return {"error": "Producto no encontrado"}
    except Exception as e:
        return {"error": str(e)}
