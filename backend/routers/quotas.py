import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from config import STORAGE_DIR

router = APIRouter()

@router.get("/quotas")
async def get_quotas_mapping():
    """Returns the mapping of Material ID -> Installment Plans"""
    mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
    
    # 1. Sync from Supabase if local is missing
    if not os.path.exists(mapping_file):
        from supabase_db import get_quotas_from_db
        try:
            cloud_mapping = await get_quotas_from_db()
            if cloud_mapping:
                with open(mapping_file, "w", encoding="utf-8") as f:
                    json.dump(cloud_mapping, f, indent=2)
                return cloud_mapping
        except: pass

    if os.path.exists(mapping_file):
        with open(mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.post("/upload-quotas")
async def upload_quotas(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload cuotas.xlsx and auto-process it"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .xlsx")
    
    quotas_path = os.path.join(STORAGE_DIR, "cuotas.xlsx")
    with open(quotas_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        from process_quotas import process_quotas
        process_quotas()
        
        mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            
            # Sync to Supabase in background
            from supabase_db import save_quotas_to_db, upload_inventory_pdf_to_supabase # We reuse upload_inventory_pdf_to_supabase for xlsx or specific one
            from fastapi import BackgroundTasks
            
            # Let's add a specialized xlsx upload if needed, or reuse
            from supabase_db import upload_spec_to_supabase # Storage logic is generic enough
            
            # Save mapping to DB
            background_tasks.add_task(save_quotas_to_db, result)
            # Save raw file to storage (bucket: inventories or a new one)
            background_tasks.add_task(upload_spec_to_supabase, quotas_path, "cuotas.xlsx")
            
            return {"message": f"Cuotas procesadas exitosamente. {len(result)} equipos mapeados.", "count": len(result)}
        return {"message": "Archivo subido pero no se pudo procesar.", "count": 0}
    except Exception as e:
        return {"message": f"Archivo subido. Error al procesar: {str(e)}", "count": 0}

@router.post("/process-quotas")
async def trigger_process_quotas():
    """Re-run quota processing with existing cuotas.xlsx"""
    quotas_path = os.path.join(STORAGE_DIR, "cuotas.xlsx")
    if not os.path.exists(quotas_path):
        raise HTTPException(status_code=404, detail="No hay archivo cuotas.xlsx en el servidor.")
    try:
        from process_quotas import process_quotas
        process_quotas()
        mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            return {"message": f"Cuotas reprocesadas. {len(result)} equipos mapeados.", "count": len(result)}
        return {"message": "Error: no se generó el archivo de mapeo.", "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
