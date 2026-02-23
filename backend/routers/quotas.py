import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import STORAGE_DIR

router = APIRouter()

@router.get("/quotas")
async def get_quotas_mapping():
    """Returns the mapping of Material ID -> Installment Plans"""
    mapping_file = os.path.join(STORAGE_DIR, "quota_mapping.json")
    if os.path.exists(mapping_file):
        with open(mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.post("/upload-quotas")
async def upload_quotas(file: UploadFile = File(...)):
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
