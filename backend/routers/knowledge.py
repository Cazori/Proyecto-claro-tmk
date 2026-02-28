import json
import pandas as pd
from fastapi import APIRouter, HTTPException
from config import KNOWLEDGE_FILE
from processor import get_latest_inventory
from supabase_db import save_knowledge_to_db, get_knowledge_from_db

router = APIRouter()

@router.get("/knowledge")
async def get_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        try:
            cloud_knowledge = await get_knowledge_from_db()
            if cloud_knowledge:
                with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cloud_knowledge, f, indent=4, ensure_ascii=False)
        except: pass
        
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

@router.post("/update-knowledge")
async def update_knowledge(entry: dict):
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sku = entry.get("sku")
        found = False
        for i, item in enumerate(data):
            if item.get("sku") == sku:
                data[i] = entry
                found = True
                break
        
        if not found:
            data.append(entry)
            
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        # Sync to Supabase
        await save_knowledge_to_db(data)
            
        return {"message": "Conocimiento actualizado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-auto-tips")
async def apply_auto_tips(data: dict):
    category = data.get("category")
    tip = data.get("tip")
    if not category or not tip:
        raise HTTPException(status_code=400, detail="Categoría y tip son obligatorios.")
    
    try:
        df = await get_latest_inventory()
        mask = df['categoria'].astype(str).str.upper() == category.upper()
        targets = df[mask]
        
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            expert_data = json.load(f)
        
        applied_count = 0
        for _, row in targets.iterrows():
            sku = str(row['Material'])
            existing = next((item for item in expert_data if item.get("sku") == sku), None)
            if existing:
                if not existing.get("tip_venta") or existing.get("tip_venta") == "-":
                    existing["tip_venta"] = tip
                    applied_count += 1
            else:
                expert_data.append({
                    "sku": sku,
                    "model": row['Subproducto'],
                    "specs": row.get('especificaciones', '-'),
                    "tip_venta": tip
                })
                applied_count += 1
        
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(expert_data, f, indent=4, ensure_ascii=False)
            
        # Sync to Supabase
        await save_knowledge_to_db(expert_data)
            
        return {"message": "Tips aplicados correctamente.", "applied": applied_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
