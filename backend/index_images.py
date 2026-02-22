import os
import asyncio
from embeddings_service import embeddings_service

SPECS_DIR = "specs"

async def index_all_images():
    print(f"--- Inciando Indexación Semántica de Imágenes en '{SPECS_DIR}' ---")
    
    if not os.path.exists(SPECS_DIR):
        print(f"Error: La carpeta '{SPECS_DIR}' no existe.")
        return

    # List all image files
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    image_files = [f for f in os.listdir(SPECS_DIR) if f.lower().endswith(valid_extensions)]
    
    print(f"Encontradas {len(image_files)} imágenes para procesar.")
    
    indexed_count = 0
    error_count = 0
    
    for idx, filename in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] Procesando: {filename}...", end=" ", flush=True)
        
        try:
            # This handles caching internally
            embedding = embeddings_service.get_image_embedding(filename)
            if embedding:
                print("✓")
                indexed_count += 1
            else:
                print("✗ (Error en API)")
                error_count += 1
        except Exception as e:
            print(f"✗ ({e})")
            error_count += 1
            
    print("\n--- Resumen de Indexación ---")
    print(f"✅ Imágenes indexadas con éxito: {indexed_count}")
    print(f"❌ Errores encontrados: {error_count}")
    print(f"Total en caché: {len(embeddings_service.cache)}")

if __name__ == "__main__":
    asyncio.run(index_all_images())
