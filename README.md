# Claro Inventario AI (Asistente "Cleo")

![Versión](https://img.shields.io/badge/version-1.9.5-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![React](https://img.shields.io/badge/react-18%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.100%2B-green.svg)

Ecosistema inteligente conversacional y panel de control administrativo diseñado para el canal de Telemercadeo (TMK) de Claro. Permite a los asesores comerciales consultar existencias físicas de inventario en bodegas críticas, visualizar precios, calcular cuotas mensuales de financiamiento y acceder a fichas técnicas oficiales mediante lenguaje natural.

---

##  Características Principales

*    **Búsqueda Híbrida Avanzada (Fast Path / AI Path):**
    *   **Fast Path:** Filtrado directo en DataFrame mediante palabras clave para respuestas inmediatas de baja latencia.
    *   **AI Path:** Análisis y clasificación de intención conversacional mediante IA para responder a consultas complejas.
*    **AIPool (Tolerancia a fallos):** Sistema de balanceo y rotación automática de APIs de lenguaje. Si falla Google Gemini, se escala la petición inmediatamente a Groq, OpenAI o Grok.
*    **Parser Inteligente de Inventarios (PDF a Base de Datos):** Extracción asíncrona de SKUs, stocks y precios con IVA mediante hilos en segundo plano para evitar bloqueos del servidor.
*    **Procesamiento de Cuotas de Financiación:** Mapeo automático de tablas financieras complejas de Claro desde archivos Excel (`.xlsx`) hacia la base de datos Postgres.
*    **Branding y Persuasión Comercial:** Generación automática de tips y speech persuasivos de venta por cada producto para apoyar al operador durante la llamada telefónica.

---

## 🛠️ Stack de Tecnologías

*   **Backend:** Python 3.10+, FastAPI, Uvicorn, Pandas, pdfplumber, Supabase Client.
*   **Modelos de Lenguaje (LLMs):** Google Gemini, Groq (Llama 3.3), OpenAI API, xAI Grok.
*   **Frontend:** React.js, Vite, Tailwind CSS.
*   **Base de Datos y Almacenamiento:** Supabase (PostgreSQL y Storage Buckets).

---

## ⚙️ Configuración del Entorno

### Requisitos
*   Python 3.10+
*   Node.js v18+

### Variables de Entorno (backend/.env)
Configura el archivo `.env` en la raíz de la carpeta `backend`:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key-de-supabase

# Configura al menos uno de los siguientes proveedores de IA:
GEMINI_API_KEY=tu-clave-de-gemini
GROQ_API_KEY=tu-clave-de-groq
OPENAI_API_KEY=tu-clave-de-openai
GROK_API_KEY=tu-clave-de-grok
