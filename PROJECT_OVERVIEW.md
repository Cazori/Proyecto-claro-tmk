# Proyecto Claro TMK – Visión General

## Qué hace el proyecto
Este es un asistente conversacional llamado **Cleo** que permite a los asesores de telemercadeo (TMK) de Claro consultar inventario físico, precios, cuotas de financiación y fichas técnicas mediante lenguaje natural. Integra búsquedas híbridas (rápida vía DataFrames y profunda vía IA), balanceo automático de LLMs y procesamiento asíncrono de PDFs y archivos Excel.

## Problema que resuelve
- **Acceso instantáneo a información de inventario** sin necesidad de navegar múltiples sistemas.
- **Reducción de tiempo y errores** al obtener precios y cálculos de cuotas rápidamente.
- **Resiliencia frente a fallos de API** mediante un pool de proveedores de IA (Gemini, Groq, OpenAI, Grok).
- **Automatización de extracción de datos** de catálogos PDF y tablas financieras Excel.

## Principales características
- **Búsqueda híbrida avanzada** (Fast Path – filtrado directo; AI Path – clasificación de intención).  
- **AIPool** con tolerancia a fallos y conmutación automática entre proveedores de IA.  
- **Parser inteligente de inventarios**: extracción asíncrona de SKUs, stocks y precios desde PDFs.  
- **Procesamiento de cuotas de financiación** a partir de archivos Excel a PostgreSQL.  
- **Generación automática de tips y speech persuasivo** para apoyar al operador en la llamada.

## Stack de Tecnologías
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pandas, pdfplumber, Supabase client.  
- **Modelos de Lenguaje (LLMs)**: Google Gemini, Groq (Llama 3.3), OpenAI, xAI Grok.  
- **Frontend**: React 18, Vite, Tailwind CSS.  
- **Base de datos y almacenamiento**: Supabase (PostgreSQL + Storage Buckets).

## Configuración rápida
1. Instalar **Python 3.10+** y **Node.js v18+**.  
2. Crear archivo `.env` en `backend/` con claves de Supabase y al menos un proveedor de IA (ver `README.md`).  
3. Ejecutar `npm install && npm run dev` en `frontend/` y `uvicorn backend.main:app --reload` en `backend/`.

---
*Esta documentación sintetiza la información de los archivos README del proyecto.*
