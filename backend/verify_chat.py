import asyncio
import os
import pandas as pd
from main import chat
from processor import PROCESSED_DATA_FILE

async def run_verification():
    print("--- VERIFICACIÓN DEL ENDPOINT /CHAT ---")
    
    # 1. Check Data Availability
    print("Omitiendo chequeo local de archivo JSON (confiando en el servidor)...")

    # 2. Test Queries
    queries = [
        "televisores samsung",
        "audifonos bluetooth",
        "patineta electrica",
        "computador portatil hp"
    ]
    
    print("\n--- PROBANDO CONSULTAS ---")
    for q in queries:
        print(f"\nConsulta: '{q}'")
        try:
            response = await chat(q)
            print(f"Respuesta Cleo: {response['response'][:200]}...") # Print first 200 chars
        except Exception as e:
            print(f"Error en chat: {e}")

if __name__ == "__main__":
    asyncio.run(run_verification())
