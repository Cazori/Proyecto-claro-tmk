import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

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

# Root endpoint
@app.get("/")
async def root():
    return {"status": "Cleo AI Online (Modular Interface) v1.9.3", "timestamp": datetime.now()}

# Register Routers
app.include_router(inventory.router, tags=["Inventory"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(specs.router, tags=["Specs"])
app.include_router(quotas.router, tags=["Quotas"])
app.include_router(knowledge.router, tags=["Knowledge"])

if __name__ == "__main__":
    print("Iniciando servidor Cleo AI Modular (v1.9.3)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
