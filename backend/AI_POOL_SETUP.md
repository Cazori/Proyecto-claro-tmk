# Guía de Configuración: Sistema de Pool de APIs Multi-Proveedor

## 🎯 ¿Qué se ha implementado?

Cleo ahora puede usar **múltiples proveedores de IA** de forma automática:
- **Gemini** (Google) - Hasta 9 cuentas simultáneas
- **Groq** - Ultra rápido (recomendado)
- **Grok** (xAI)
- **OpenAI** (opcional)
- **Claude** (opcional)

### Características
✅ Rotación automática cuando una API alcanza su cuota  
✅ Tracking de rendimiento en tiempo real  
✅ 3 estrategias de rotación (Fallback, Round-Robin, Fastest-First)  
✅ Dashboard de métricas en `/api/pool-stats`  

---

## 📋 Pasos para Configurar

### 1. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

Esto instalará:
- `httpx` - Para llamadas HTTP asíncronas
- `google-generativeai` - SDK de Gemini
- `openai` - SDK de OpenAI (opcional)

### 2. Obtener API Keys

#### **Gemini (Google)** - RECOMENDADO
1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crea una API key (o varias si quieres más cuota)
3. Copia las keys

**Cuota gratuita:** 15-20 req/min por key

#### **Groq** - ULTRA RÁPIDO (Recomendado)
1. Ve a [Groq Console](https://console.groq.com/keys)
2. Crea una cuenta (gratis)
3. Genera una API key

**Cuota gratuita:** 30 req/min, 500 tokens/seg

#### **Grok (xAI)** - Opcional
1. Ve a [xAI Console](https://console.x.ai/)
2. Solicita acceso a la API
3. Genera una key

**Nota:** Requiere aprobación

#### **OpenAI** - Opcional
1. Ve a [OpenAI Platform](https://platform.openai.com/api-keys)
2. Crea una API key

**Nota:** Requiere créditos de pago

---

### 3. Configurar el archivo `.env`

Abre el archivo `.env` en la carpeta `backend` y añade tus keys:

```env
# Gemini - Puedes añadir hasta 9 cuentas
GEMINI_API_KEY_1=AIzaSy...tu_primera_key
GEMINI_API_KEY_2=AIzaSy...tu_segunda_key
GEMINI_API_KEY_3=AIzaSy...tu_tercera_key

# Groq (Recomendado para velocidad)
GROQ_API_KEY=gsk_...tu_groq_key

# Grok (Opcional)
GROK_API_KEY=xai-...tu_grok_key

# OpenAI (Opcional)
OPENAI_API_KEY=sk-...tu_openai_key

# Configuración del Pool
AI_POOL_STRATEGY=fallback
```

**¿Cuántas keys necesitas?**
- **Mínimo:** 1 key de Gemini (ya la tienes)
- **Recomendado:** 2-3 keys de Gemini + 1 de Groq
- **Óptimo:** 3 Gemini + 1 Groq + 1 Grok

---

### 4. Estrategias de Rotación

Puedes cambiar `AI_POOL_STRATEGY` en el `.env`:

| Estrategia | Descripción | Cuándo usar |
|------------|-------------|-------------|
| `fallback` | Usa la API principal hasta que falle, luego cambia | **Recomendado** - Máxima estabilidad |
| `round_robin` | Alterna entre todas las APIs equitativamente | Balanceo de carga |
| `fastest` | Siempre usa la API más rápida | Priorizar velocidad |

---

### 5. Probar el Sistema

#### Opción A: Test Script
```bash
cd backend
python test_ai_pool.py
```

Esto mostrará:
- ✅ Qué proveedores se cargaron correctamente
- 📊 Estadísticas de rendimiento
- ⚡ Latencia de cada proveedor

#### Opción B: Endpoint de Stats
Inicia el servidor:
```bash
python main.py
```

Luego visita: `http://localhost:8000/api/pool-stats`

Verás algo como:
```json
{
  "providers": [
    {
      "name": "gemini-1",
      "stats": {
        "total_requests": 45,
        "successful": 43,
        "avg_latency_ms": 850
      }
    },
    {
      "name": "groq-llama",
      "stats": {
        "total_requests": 12,
        "successful": 12,
        "avg_latency_ms": 320
      }
    }
  ],
  "strategy": "fallback",
  "total_providers": 2
}
```

---

### 6. Verificar que Funciona

1. Inicia el servidor: `python main.py`
2. Deberías ver en la consola:
   ```
   ✓ Loaded Gemini provider #1
   ✓ Loaded Gemini provider #2
   ✓ Loaded Groq provider (ultra-fast)
   
   🎯 AI Pool initialized with 3 provider(s)
   ✓ AI Pool initialized successfully
   ```

3. Haz una consulta en Cleo
4. En la consola verás:
   ```
   🤖 Trying gemini-1...
   ```

5. Si `gemini-1` falla por cuota, automáticamente intentará con `gemini-2`, luego `groq`, etc.

---

## 🔍 Monitoreo de Rendimiento

El sistema guarda estadísticas en `performance_tracker.json`:

```json
{
  "gemini-1": {
    "total_requests": 150,
    "successful": 145,
    "failed": 5,
    "avg_latency_ms": 850,
    "last_error": "429 - Quota exceeded",
    "last_used": "2026-02-13T23:30:00"
  },
  "groq-llama": {
    "total_requests": 50,
    "successful": 50,
    "failed": 0,
    "avg_latency_ms": 320,
    "last_error": null
  }
}
```

Esto te permite:
- Ver qué proveedor es más rápido
- Detectar cuál falla más
- Optimizar tu configuración

---

## ⚠️ Solución de Problemas

### "No AI providers configured"
- Verifica que el `.env` tiene al menos una API key válida
- Asegúrate de que el archivo `.env` está en la carpeta `backend`

### "Failed to load Gemini #1"
- La API key es inválida
- Verifica que copiaste la key completa

### "All AI providers failed"
- Todas las APIs alcanzaron su cuota
- Espera unos minutos o añade más keys

### El pool no se inicializa
- Revisa la consola para ver el error exacto
- El sistema automáticamente usará el modelo Gemini único como fallback

---

## 🚀 Próximos Pasos (Opcional)

1. **Añadir más keys de Gemini** para multiplicar la cuota
2. **Activar Groq** para respuestas ultra-rápidas
3. **Monitorear `/api/pool-stats`** para optimizar

---

## 📞 Resumen Rápido

**Para empezar ahora mismo:**
1. Abre `.env`
2. Añade al menos 2-3 keys de Gemini:
   ```env
   GEMINI_API_KEY_1=tu_key_1
   GEMINI_API_KEY_2=tu_key_2
   ```
3. Reinicia el servidor: `python main.py`
4. ¡Listo! Cleo ahora tiene el doble/triple de cuota

**Para máxima velocidad:**
1. Crea cuenta en [Groq](https://console.groq.com)
2. Añade la key al `.env`:
   ```env
   GROQ_API_KEY=gsk_tu_key
   ```
3. Reinicia
4. Groq responderá en ~300ms vs ~850ms de Gemini
