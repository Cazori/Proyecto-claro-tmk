import pdfplumber
import pandas as pd
import os
import glob
import asyncio
import re
from datetime import datetime
from dotenv import load_dotenv
import json
import gc
import sys

# Load environment variables
load_dotenv()

# AI Pool will be injected from main.py
_ai_pool = None

# Global In-Memory Cache for performance
_inventory_cache = None
_inventory_cache_mtime = 0
_inventory_lock = asyncio.Lock()

# Import Supabase logic
from supabase_db import save_inventory_to_db, get_inventory_from_db

def set_ai_pool(pool):
    """Set the AI pool instance for normalization"""
    global _ai_pool
    _ai_pool = pool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
PROCESSED_DATA_FILE = os.path.join(STORAGE_DIR, "processed_inventory.json")
NORMALIZATION_CACHE_FILE = os.path.join(STORAGE_DIR, "normalization_cache.json")
MAX_FILES = 5

async def normalize_products_batch(descriptions):
    """
    Desactivado a petición del usuario para evitar gastos de API y lentitud.
    """
    return {}

def rule_based_normalization(desc):
    """Fallback logic for common brands and categories using keywords"""
    desc_upper = desc.upper()
    res = {"categoria": "N/A", "marca": "N/A", "modelo_limpio": desc, "especificaciones": ""}
    
    # Category detection
    if any(k in desc_upper for k in ["TV", "TELEVIS"]): res["categoria"] = "TV"
    elif any(k in desc_upper for k in ["PRT", "PORT", "LAPTOP"]): res["categoria"] = "Laptop"
    elif any(k in desc_upper for k in ["TAB", "IPAD"]): res["categoria"] = "Tablet"
    elif any(k in desc_upper for k in ["CEL", "SMARTPHONE", "MOTO", "IPHONE"]): res["categoria"] = "Celular"
    elif any(k in desc_upper for k in ["PATINETA"]): res["categoria"] = "Patineta"
    elif any(k in desc_upper for k in ["AUD", "BUDS", "AURIC", "AUDF", "AUDIF"]): res["categoria"] = "Audífonos"
    elif any(k in desc_upper for k in ["WATCH", "SMRT", "CLOCK"]): res["categoria"] = "Reloj"
    elif any(k in desc_upper for k in ["TRRE", "TORRE"]): res["categoria"] = "Torre Sonido"
    
    # Brand detection
    brands = {
        "SAMS": "Samsung", "SAMSUNG": "Samsung",
        "HUAW": "Huawei", "HUAWEI": "Huawei",
        "MOT": "Motorola", "MOTOROLA": "Motorola",
        "XIAO": "Xiaomi", "XIAOMI": "Xiaomi",
        "HEWP": "HP", "HP": "HP",
        "LENO": "Lenovo", "LENOVO": "Lenovo",
        "ASUS": "Asus",
        "APPL": "Apple", "IPHONE": "Apple", "IPAD": "Apple", "APPLE": "Apple",
        "TCL": "TCL",
        "NIU": "NIU",
        "HONOR": "Honor"
    }
    for k, v in brands.items():
        if f" {k}" in f" {desc_upper}" or f"{k} " in f"{desc_upper} " or desc_upper.endswith(k):
            res["marca"] = v
            break
            
    return res

async def process_inventory_pdf(file_path):
    """
    Extracts data from PDF and normalizes it using AI for categorization/specs.
    Returns a DataFrame.
    """
    try:
        data = []
        if not os.path.exists(file_path):
            return None

        with pdfplumber.open(file_path) as pdf:
            page_bodega = "CEM Bogotá - ZF" # Default
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text: continue
                
                # Robust Bodega detection
                text_upper = text.upper()
                if any(k in text_upper for k in ["ZF", "BOGOTÁ", "BOGOTA", "CEM BOG"]):
                    page_bodega = "CEM Bogotá - ZF"
                elif any(k in text_upper for k in ["CAVA", "MEDELLÍN", "MEDELLIN"]):
                    page_bodega = "CAVA Medellín"
                
                # Process line by line
                lines = text.split('\n')
                page_count = 0
                for line in lines:
                    # Robust Pattern 2-step: ID -> Name -> Total -> Disponible -> Categoria -> everything after "Aplica $"
                    # Group 5 is the native Category.
                    pattern_v3 = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+)\s*(.*?)\s*Aplica\s+\$(.*)"
                    
                    # Fallback for lines without "Aplica $" 
                    pattern_flex = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+)\s*(.*?)\s*\$?\s?(\d{1,3}(?:\.\d{3})*(?:,\d+)?|[-])"

                    match = re.search(pattern_v3, line)
                    if match:
                        material = match.group(1)
                        subproducto = match.group(2).strip()
                        stock = match.group(3) 
                        categoria_nativa = match.group(5).strip()
                        tail = match.group(6)
                        
                        # Find all number sequences in the tail (including single digits)
                        # We prioritize the LAST one as the Total Value
                        prices = re.findall(r"(\d[\d\.\s,]*\d|\d)", tail)
                        if prices:
                            price_raw = prices[-1]
                        else:
                            price_raw = "-" if "-" in tail else "0"
                    else:
                        match = re.search(pattern_flex, line)
                        if match:
                            material = match.group(1)
                            subproducto = match.group(2).strip()
                            stock = match.group(3)
                            categoria_nativa = match.group(5).strip()
                            price_raw = match.group(6).strip()
                        else:
                            continue
                    
                    # Handle hyphenated prices
                    if price_raw == "-":
                        precio_clean = "0"
                    else:
                        # Clean spaces and handle decimals (commas)
                        # Example: "3 .299.900,0" -> "3.299.900"
                        p_no_spaces = price_raw.replace(" ", "")
                        if "," in p_no_spaces:
                            p_no_spaces = p_no_spaces.split(",")[0]
                        
                        precio_clean = re.sub(r'[^\d]', '', p_no_spaces)
                        
                        # Safety check for concatenated values (standard price is ~7 digits)
                        if len(precio_clean) > 8:
                            precio_clean = precio_clean[:7]
                    
                    data.append({
                        "Bodega": page_bodega,
                        "Material": material,
                        "Subproducto": subproducto,
                        "categoria_nativa": categoria_nativa,
                        "CantDisponible": float(stock) if stock else 0,
                        "Precio Contado": float(precio_clean) if precio_clean else 0
                    })
                    page_count += 1
                
                if page_count > 0:
                    print(f"📄 Página {i+1}: Encontrados {page_count} productos ({page_bodega})")
        
        print(f"📊 DEBUG: Total items extraídos del PDF: {len(data)}")
        if not data:
            return None

        df = pd.DataFrame(data)
        
        # CENSUS - Global before filter
        bodega_census = df["Bodega"].value_counts().to_dict()
        print(f"📈 Resumen por Bodega (Pre-filtro): {bodega_census}")

        if not df.empty and "Bodega" in df.columns:
            # Allow "BOGOT", "ZF", or "CEM BOG"
            df = df[df["Bodega"].astype(str).str.upper().str.contains("BOGOT|ZF|BOG")]
            print(f"⚖️ Filtrado estricto: BOGOTÁ/ZF. Items finales: {len(df)}")
        
        df = df.drop_duplicates(subset=["Material", "Subproducto", "CantDisponible"])
        
        # --- Lightweight Normalization ---
        # Skip AI and get native categories, use simple rule-based for the rest
        df["categoria"] = df["categoria_nativa"]
        df["marca"] = df["Subproducto"].apply(lambda x: rule_based_normalization(x).get("marca", "N/A"))
        df["modelo_limpio"] = df["Subproducto"]
        df["especificaciones"] = "-"
        df["tip_venta"] = "-"

        # Save in new format with metadata
        now = datetime.now().isoformat()
        inventory_payload = {
            "last_update": now,
            "records": df.to_dict('records')
        }
        with open(PROCESSED_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(inventory_payload, f, ensure_ascii=False, indent=4)
        
        # Invalidate cache so it's reloaded on next call
        global _inventory_cache
        _inventory_cache = None
        
        # PERSISTENCE: Save to Supabase (Wait for it)
        await save_inventory_to_db(df)
        
        print(f"Éxito: {len(df)} ítems procesados.")
        
        # Explicitly clear temporary objects
        del data
        gc.collect()
        
        return df

    except Exception as e:
        print(f"Error en procesamiento híbrido: {e}")
        return None

def rotate_inventories():
    """
    Keeps only the most recent 5 files.
    NOTE: Removed deletion of PROCESSED_DATA_FILE to avoid 'reversion' to old data
    if a background task takes time or fails. Data will be overwritten when new
    processing actually COMPLETES.
    """
    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if len(files) <= MAX_FILES:
        return

    files.sort(key=os.path.getmtime)
    for i in range(len(files) - MAX_FILES):
        try:
            os.remove(files[i])
            print(f"Limpieza: Eliminado PDF antiguo {files[i]}")
        except: pass

async def get_latest_inventory():
    """
    Returns the most recent processed DataFrame with in-memory caching and request deduplication.
    """
    global _inventory_cache, _inventory_cache_mtime
    
    async with _inventory_lock:
        local_pdfs = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
        latest_pdf = max(local_pdfs, key=os.path.getmtime) if local_pdfs else None
        
        # 1. SUPABASE SYNC CHECK (Source of Truth)
        # Check if Supabase has a newer version than our local JSON
        from supabase_db import get_metadata_db, get_inventory_from_db
        try:
            metadata = await get_metadata_db()
            if metadata and metadata.get("last_update"):
                cloud_mtime = datetime.fromisoformat(metadata["last_update"]).timestamp()
                
                # If cloud is newer OR we are missing local JSON, sync it
                should_sync = not os.path.exists(PROCESSED_DATA_FILE)
                if not should_sync:
                    try:
                        with open(PROCESSED_DATA_FILE, "r", encoding="utf-8") as f:
                            local_data = json.load(f)
                            if isinstance(local_data, dict) and "last_update" in local_data:
                                local_mtime = datetime.fromisoformat(local_data["last_update"]).timestamp()
                            else:
                                local_mtime = os.path.getmtime(PROCESSED_DATA_FILE)
                            
                            if cloud_mtime > local_mtime + 5: # 5s buffer
                                print("☁ Supabase tiene una versión más reciente. Sincronizando...")
                                should_sync = True
                    except:
                        should_sync = True
                
                if should_sync:
                    print("☁ Sincronizando inventario desde Supabase DB...")
                    cloud_df = await get_inventory_from_db(columns="*")
                    if cloud_df is not None and not cloud_df.empty:
                        inventory_payload = {
                            "last_update": metadata.get("last_update"),
                            "records": cloud_df.to_dict('records')
                        }
                        with open(PROCESSED_DATA_FILE, "w", encoding="utf-8") as f:
                            json.dump(inventory_payload, f, ensure_ascii=False, indent=4)
                        _inventory_cache = cloud_df
                        _inventory_cache_mtime = cloud_mtime
                        return _inventory_cache
        except Exception as e:
            print(f"! Error sincronizando con Supabase: {e}")

        # 2. IN-MEMORY CACHE
        if _inventory_cache is not None:
            if latest_pdf:
                pdf_mtime = os.path.getmtime(latest_pdf)
                if _inventory_cache_mtime >= pdf_mtime:
                    return _inventory_cache

        # 3. LOCAL JSON (Disk Cache)
        if os.path.exists(PROCESSED_DATA_FILE):
            try:
                with open(PROCESSED_DATA_FILE, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                
                if isinstance(local_data, dict) and "records" in local_data:
                    local_df = pd.DataFrame(local_data["records"])
                    json_mtime = datetime.fromisoformat(local_data.get("last_update", datetime.now().isoformat())).timestamp()
                else:
                    local_df = pd.DataFrame(local_data) # Legacy support
                    json_mtime = os.path.getmtime(PROCESSED_DATA_FILE)

                if latest_pdf:
                    pdf_mtime = os.path.getmtime(latest_pdf)
                    if json_mtime >= pdf_mtime:
                        print("✓ Cargando inventario local (Caché disco).")
                        _inventory_cache = local_df
                        _inventory_cache_mtime = json_mtime
                        return _inventory_cache
                else:
                    print("✓ Cargando inventario local (Caché disco - sin PDF).")
                    _inventory_cache = local_df
                    _inventory_cache_mtime = json_mtime
                    return _inventory_cache
            except Exception as e:
                print(f"Error cargando JSON local: {e}")

        # 4. LOCAL PDF PROCESSING (Last resort)
        if latest_pdf:
            print(f"Procesando PDF local más reciente: {latest_pdf}")
            _inventory_cache = await process_inventory_pdf(latest_pdf)
            if _inventory_cache is not None:
                _inventory_cache_mtime = os.path.getmtime(latest_pdf)
            return _inventory_cache

        return None
