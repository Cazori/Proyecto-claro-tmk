import os
import shutil
import pandas as pd
import json
import re
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import STORAGE_DIR

router = APIRouter()

SALES_FILE_PATH = os.path.join(STORAGE_DIR, "Claroges.csv")

def clean_search_term(term: str) -> str:
    """Removes spaces and non-alphanumeric characters for clean matching."""
    return re.sub(r'[\s\.\-,]', '', str(term)).lower()

@router.post("/upload-sales")
async def upload_sales(file: UploadFile = File(...)):
    """Uploads a new sales file (CSV or Excel) and converts it to the standard Claroges.csv format."""
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Formato no soportado. Sube un archivo CSV o Excel.")
    
    temp_path = os.path.join(STORAGE_DIR, f"temp_sales.{ext}")
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Predict separator and encoding if CSV, or use read_excel
        if ext == "csv":
            df = pd.read_csv(temp_path, sep=';', encoding='latin1')
        else:
            df = pd.read_excel(temp_path)
            
        # Standardize columns to upper
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Save as our unified CSV format
        df.to_csv(SALES_FILE_PATH, sep=';', encoding='latin1', index=False)
        
        os.remove(temp_path)
        return {"message": "Base de ventas actualizada correctamente.", "records": len(df)}
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

@router.get("/sales/search")
async def search_sales(q: str):
    """Searches sales by cleaned Cedula or exact/partial Asesor Name."""
    if not os.path.exists(SALES_FILE_PATH):
        raise HTTPException(status_code=404, detail="La base de ventas no ha sido cargada.")
        
    if not q or len(q.strip()) < 3:
        return []
        
    try:
        # Load the CSV
        df = pd.read_csv(SALES_FILE_PATH, sep=';', encoding='latin1')
        
        # Normalize columns just in case
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        query_clean = clean_search_term(q)
        is_numeric = query_clean.isdigit()
        
        results = []
        
        # Find matches
        for _, row in df.iterrows():
            match = False
            
            # Check Cedula
            cedula_val = str(row.get("CÉDULA ASESOR", row.get("CEDULA ASESOR", "")))
            if is_numeric and query_clean in clean_search_term(cedula_val):
                match = True
            
            # Check Name
            if not is_numeric:
                asesor_name = str(row.get("ASESOR", ""))
                # Remove extra spaces and compare lower
                asesor_name_clean = " ".join(asesor_name.lower().split())
                query_name_clean = " ".join(q.lower().split())
                
                if query_name_clean in asesor_name_clean:
                    match = True
                    
            if match:
                # Compile response format
                results.append({
                    "document": str(row.get("NÚMERO DOCUMENTO", row.get("NUMERO DOCUMENTO", ""))),
                    "code": str(row.get("CÓDIGO", row.get("CODIGO", ""))),
                    "status": str(row.get("ESTADO ACTUAL", "")),
                    "delivery_date": str(row.get("FECHA ENTREGA", "")),
                    "product": str(row.get("DESCRIPCIÓN PRODUCTO", row.get("PRODUCTO", ""))),
                    "client": str(row.get("CLIENTE", ""))
                })
        
        # We don't want to choke the frontend with 10k results if query is too broad
        return results[:100]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la búsqueda: {str(e)}")
