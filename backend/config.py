import os
import json
from dotenv import load_dotenv
from ai_pool import AIPool, RotationStrategy

# Load environment variables
load_dotenv()

# Path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
SPECS_DIR = os.path.join(BASE_DIR, "specs")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "expert_knowledge.json")
SPECS_MAPPING_FILE = os.path.join(STORAGE_DIR, "specs_mapping.json")
QUOTA_MAPPING_FILE = os.path.join(STORAGE_DIR, "quota_mapping.json")

# Ensure directories exist
for d in [STORAGE_DIR, SPECS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Initialize knowledge base file if missing
if not os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# Global AI Pool (Eager Initialization with Validation)
_ai_pool = None

def get_ai_pool():
    """Returns the AI Pool. Initializes and validates on first call."""
    global _ai_pool
    if _ai_pool is None:
        try:
            from ai_pool import AIPool, RotationStrategy
            print("🚀 Initializing AI Pool...")
            _ai_pool = AIPool(strategy=RotationStrategy.FALLBACK)
            
            # VALIDACIÓN ESTRICTA: debe haber al menos 1 proveedor funcional
            if not _ai_pool.providers:
                raise RuntimeError(
                    "No hay proveedores de IA configurados. "
                    "Verifica GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, GROK_API_KEY en .env"
                )
            
            print(f"✓ AI Pool listo con {len(_ai_pool.providers)} proveedor(es): "
                  f"{[p.name for p in _ai_pool.providers]}")
                  
        except Exception as e:
            print(f"✗ CRITICAL: AI Pool initialization failed: {e}")
            raise  # Falla rápido — la app no debe arrancar sin IA
    return _ai_pool

# Shared Nomenclature & Constants
SYNONYMS = {
    "port": "portatil", "portatil": "prt", "portatiles": "prt", "laptop": "prt", "laptops": "prt",
    "hp": "hewp", "hewlett": "hewp", "packard": "hewp", "ng": "negro", "ngr": "negro",
    "bl": "blanco", "blnc": "blanco", "cel": "celular", "celulares": "celular",
    "tel": "telefono", "telefonos": "celular", "aud": "aud", "audifono": "aud", "audifonos": "aud",
    "auricular": "aud", "auriculares": "aud", "cascos": "aud", "buds": "aud",
    "smrt": "smart", "watch": "reloj", "sw": "reloj", "tablet": "tab", "tablets": "tab",
    "ryzen": "rzn", "intel": "ic", "core": "ic", "ram": "g", "gb": "g"
}

NOISE_WORDS = {"ngr", "grs", "slv", "negro", "gris", "silver", "pulg", "pulgadas", "inches", "smart"}
