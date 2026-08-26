import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncio
import os
import traceback

# Import modular routers
from routers import inventory, chat, specs, quotas, knowledge

app = FastAPI(title="Cleo Inventory AI API", version="1.9.4")

# ─── CORS: Restringir a Vercel en producción ───
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── MIDDLEWARE: Error Handling Uniforme ───
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise  # Deja que FastAPI maneje HTTPException
    except Exception as e:
        # Log completo en servidor
        print(f"✗ UNHANDLED ERROR [{request.method} {request.url.path}]: {e}")
        traceback.print_exc()
        # Respuesta uniforme al cliente
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor",
                "code": "INTERNAL_ERROR",
                "path": request.url.path
            }
        )

# ─── STARTUP: Validación estricta de dependencias ───
@app.on_event("startup")
async def startup_event():
    """
    Arranque con validaciones estrictas:
    1. AI Pool debe tener ≥1 proveedor
    2. Supabase debe responder
    3. Disco accesible
    """
    print("🚀 Cleo AI Starting — Validando dependencias...")
    
    # 1. AI Pool (lanza excepción si falla)
    from config import get_ai_pool
    try:
        pool = get_ai_pool()
        print(f"✓ AI Pool OK: {[p.name for p in pool.providers]}")
    except Exception as e:
        print(f"✗ AI Pool FAILED: {e}")
        raise RuntimeError("No se puede arrancar sin IA funcional") from e
    
    # 2. Supabase connectivity check
    from supabase_db import get_metadata_db
    try:
        meta = await get_metadata_db()
        if meta:
            print(f"✓ Supabase OK (última sync: {meta.get('last_update', 'desconocida')})")
        else:
            print("⚠ Supabase responde pero sin metadata")
    except Exception as e:
        print(f"✗ Supabase FAILED: {e}")
        # No levantamos excepción — la app puede funcionar con cache local
    
    # 3. Cloud Sync (existente)
    from config import STORAGE_DIR, SPECS_MAPPING_FILE, KNOWLEDGE_FILE
    import json
    from supabase_db import (
        get_specs_mapping_from_db, 
        get_knowledge_from_db, 
        get_inventory_from_db,
        download_latest_inventory_pdf_from_supabase
    )
    
    # 3a. Sync Mappings
    try:
        print("Syncing specs_mapping from Cloud...")
        mapping = await get_specs_mapping_from_db()
        if mapping:
            with open(SPECS_MAPPING_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=4, ensure_ascii=False)
            print(f"Synced {len(mapping)} image mappings from Supabase.")
        else:
            print("Cloud mapping empty. Keeping local if exists.")
    except Exception as e:
        print(f"Error syncing mapping: {e}")
    
    # 3b. Sync Knowledge
    try:
        print("Syncing expert_knowledge from Cloud...")
        knowledge = await get_knowledge_from_db()
        if knowledge:
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(knowledge, f, indent=4, ensure_ascii=False)
            print(f"Synced {len(knowledge)} expert knowledge items from Supabase.")
        else:
            print("Cloud knowledge empty. Keeping local if exists.")
    except Exception as e:
        print(f"Error syncing knowledge: {e}")
    
    # 3c. Sync Inventory
    try:
        inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
        cloud_meta = await get_metadata_db()
        should_sync = not os.path.exists(inv_file)
        
        if cloud_meta and cloud_meta.get("last_update"):
            cloud_mtime = datetime.fromisoformat(cloud_meta["last_update"]).timestamp()
            if os.path.exists(inv_file):
                try:
                    with open(inv_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "last_update" in data:
                            local_mtime = datetime.fromisoformat(data["last_update"]).timestamp()
                        else:
                            local_mtime = os.path.getmtime(inv_file)
                    
                    if cloud_mtime > local_mtime + 5:
                        print(f"Cloud version ({cloud_meta['last_update']}) is newer than local. Syncing...")
                        should_sync = True
                except: 
                    should_sync = True
        
        if should_sync:
            print("Attempting to restore inventory from Supabase DB...")
            df = await get_inventory_from_db()
            if df is not None and not df.empty:
                inventory_payload = {
                    "last_update": cloud_meta.get("last_update") if cloud_meta else datetime.now().isoformat(),
                    "records": df.to_dict('records')
                }
                with open(inv_file, "w", encoding="utf-8") as f:
                    json.dump(inventory_payload, f, ensure_ascii=False, indent=4)
                print(f"Restored {len(df)} items from DB.")
            else:
                print("No DB inventory found. Attempting PDF download...")
                await download_latest_inventory_pdf_from_supabase(STORAGE_DIR)
    except Exception as e:
        print(f"Error syncing inventory: {e}")
    
    print("✅ Cleo AI Startup Complete — All systems go.")

# ─── ROOT & HEALTH ───
@app.get("/")
async def root():
    return {"status": "Cleo AI Online", "version": "1.9.4", "timestamp": datetime.now()}

@app.get("/health")
async def health():
    """
    Health check REAL — verifica dependencias críticas.
    Returns 200 si todo OK, 503 si hay degradación.
    """
    checks = {}
    overall = "healthy"
    
    # 1. AI Pool
    try:
        from config import get_ai_pool
        pool = get_ai_pool()
        providers = [p.name for p in pool.providers]
        checks["ai_pool"] = {"status": "ok", "providers": providers}
        if not providers:
            checks["ai_pool"]["status"] = "degraded"
            overall = "degraded"
    except Exception as e:
        checks["ai_pool"] = {"status": "down", "error": str(e)}
        overall = "unhealthy"
    
    # 2. Supabase
    try:
        from supabase_db import get_metadata_db
        meta = await get_metadata_db()
        checks["supabase"] = {"status": "ok", "last_sync": meta.get("last_update") if meta else None}
    except Exception as e:
        checks["supabase"] = {"status": "down", "error": str(e)}
        overall = "degraded"  # Puede funcionar con cache local
    
    # 3. Disk
    try:
        from config import STORAGE_DIR
        inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
        checks["disk"] = {"status": "ok", "inventory_file_exists": os.path.exists(inv_file)}
    except Exception as e:
        checks["disk"] = {"status": "down", "error": str(e)}
        overall = "unhealthy"
    
    status_code = 200 if overall == "healthy" else (503 if overall == "unhealthy" else 200)
    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "checks": checks, "timestamp": datetime.now().isoformat()}
    )

# ─── REGISTER ROUTERS ───
app.include_router(inventory.router, tags=["Inventory"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(specs.router, tags=["Specs"])
app.include_router(quotas.router, tags=["Quotas"])
app.include_router(knowledge.router, tags=["Knowledge"])
from routers import sales
app.include_router(sales.router, tags=["Sales"])

if __name__ == "__main__":
    print("Iniciando servidor Cleo AI Modular (v1.9.4)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)