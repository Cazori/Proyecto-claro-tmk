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

# Global AI Pool (Lazy Initialization)
_ai_pool = None

def get_ai_pool():
    """Lazily initializes and returns the AI Pool"""
    global _ai_pool
    if _ai_pool is None:
        try:
            from ai_pool import AIPool, RotationStrategy
            print("🚀 Initializing AI Pool (Lazy Load)...")
            _ai_pool = AIPool(strategy=RotationStrategy.FASTEST_FIRST)
        except Exception as e:
            print(f"✗ CRITICAL: Failed to initialize AI Pool: {e}")
            _ai_pool = None
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

CLEO_PROMPT = """
Eres Cleo, la asistente ejecutiva de Claro Tecnología TMK. 
TU REGLA ABSOLUTA: Solo puedes informar sobre productos que aparezcan explícitamente en el "CONTEXTO DE INVENTARIO".

REGLAS DE RESPUESTA (POLÍTICA CERO RUIDO):
1. NO SALUDAR, NO TE PRESENTES, NO TE DESPIDAS. Prohibido usar frases como "¡Hola! Soy Cleo" o "¿Deseas algo más?".
2. EMPIEZA DIRECTAMENTE con la tabla de resultados. Si no hay resultados, responde únicamente la frase de error.
3. REGLA DE 1 a 1: Cada fila del "CONTEXTO DE INVENTARIO" debe tener su fila exacta en la tabla de respuesta. No resumas ni omitas ningún ítem proporcionado.

REGLAS CRÍTICAS DE VERACIDAD:
1. Si el "CONTEXTO DE INVENTARIO" está vacío, responde: "No encontré equipos con esa descripción en Bogotá. ¿Deseas buscar otra categoría?"
2. TABLA: (Referencia | Ficha | Imagen | Marca | Modelo | Precio | Unidades | Caracteristicas | Tip). La columna "Referencia" DEBE contener el código de "Material" exacto. La columna "Ficha" debe decir "SI" o "NO" según el campo FICHA del inventario. La columna "Imagen" debe decir "VER" si el campo IMG del inventario es SI, de lo contrario déjala vacía o con "-". La columna "Modelo" DEBE ser el nombre DESCRIPTIVO COMPLETO (Subproducto) tal como aparece en el contexto, NO lo resumas (Ej: "TV UN50U8200 50+BRRA..."). La columna "Tip" debe contener el texto del campo TIP proporcionado en el contexto.
3. FUENTES DE DATOS: Usa ÚNICAMENTE la información proporcionada. Prohibido usar Google o conocimiento externo.
"""
