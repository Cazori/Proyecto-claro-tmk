import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import os

# Import modular routers
from routers import inventory, chat, specs, quotas, knowledge

app = FastAPI(title="Cleo Inventory AI API")

# CORS and Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & Health endpoints
@app.get("/")
async def root():
    return {"status": "Cleo AI Online (Modular Interface) v1.9.3", "timestamp": datetime.now()}

@app.get("/health")
async def health():
    """Diligent health check for Render"""
    return {"status": "ok", "uptime": "active"}

# --- STARTUP SYNC ---
@app.on_event("startup")
async def startup_event():
    """
    On Render startup:
    1. Restore specs_mapping.json from Supabase
    2. Restore expert_knowledge.json from Supabase
    3. Try to restore processed_inventory.json or download PDF
    """
    print("🌅 Starting Cleo AI Cloud Sync...")
    from config import STORAGE_DIR, SPECS_MAPPING_FILE, KNOWLEDGE_FILE
    import json
    from supabase_db import (
        get_specs_mapping_from_db, 
        get_knowledge_from_db, 
        get_inventory_from_db,
        download_latest_inventory_pdf_from_supabase
    )
    
    # 1. Sync Mappings
    if not os.path.exists(SPECS_MAPPING_FILE):
        print("☁ Syncing specs_mapping from Cloud...")
        mapping = await get_specs_mapping_from_db()
        if mapping:
            with open(SPECS_MAPPING_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=4)
    
    # 2. Sync Knowledge
    if not os.path.exists(KNOWLEDGE_FILE):
        print("☁ Syncing expert_knowledge from Cloud...")
        knowledge = await get_knowledge_from_db()
        if knowledge:
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(knowledge, f, indent=4)
                
    # 3. Sync Inventory (Try DB first, it's faster than PDF)
    inv_file = os.path.join(STORAGE_DIR, "processed_inventory.json")
    if not os.path.exists(inv_file):
        print("☁ Attempting to restore inventory from Supabase DB...")
        df = await get_inventory_from_db()
        if df is not None and not df.empty:
            df.to_json(inv_file, orient="records", force_ascii=False, indent=4)
            print(f"✓ Restored {len(df)} items from DB.")
        else:
            # Try PDF as last resort
            print("☁ No DB inventory found. Attempting PDF download...")
            await download_latest_inventory_pdf_from_supabase(STORAGE_DIR)
    
    print("✅ Cleo AI Cloud Sync Complete.")

# Register Routers
app.include_router(inventory.router, tags=["Inventory"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(specs.router, tags=["Specs"])
app.include_router(quotas.router, tags=["Quotas"])
app.include_router(knowledge.router, tags=["Knowledge"])

if __name__ == "__main__":
    print("Iniciando servidor Cleo AI Modular (v1.9.3)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
