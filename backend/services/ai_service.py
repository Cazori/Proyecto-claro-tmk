import json
from config import ai_pool

class AIService:
    @staticmethod
    async def generate_response(prompt: str) -> str:
        """Generates a response using the AI pool."""
        if not ai_pool:
            return ""
        return await ai_pool.generate(prompt)

    @staticmethod
    async def analyze_intent(query: str) -> dict:
        """Analyzes the user's search intent."""
        intent_prompt = f"""
        Eres un experto en clasificar intenciones de búsqueda para un inventario de tecnología.
        CAMPOS DISPONIBLES EN BD:
        - categoria: (TV, Celular, Laptop, Reloj, Audífonos, Parlante, Patineta, Tablet, Accesorio, Otro)
        - marca: (Samsung, Apple, HP, Lenovo, Xiaomi, Huawei, Honor, Sony, etc.)
        - modelo: (Referencia específica o palabras clave del producto)
        
        CONSULTA USUARIO: "{query}"
        TU TAREA: Extrae los valores para filtrar. 
        REGLA CRÍTICA PARA TV: Si el usuario busca pulgadas, el campo 'modelo' DEBE incluir el número seguido de comilla doble (ej: '50"').
        EJEMPLOS: "iphone 15" -> {{"marca": "Apple", "modelo": "iphone 15", "categoria": "Celular"}}
        Responde ÚNICAMENTE en JSON.
        """
        
        try:
            if ai_pool:
                response_text = await ai_pool.generate(intent_prompt)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(response_text)
        except Exception as e:
            print(f"Error AIService.analyze_intent: {e}")
        
        return {"categoria": None, "marca": None, "modelo": None}

    @staticmethod
    async def generate_sales_tip(model_name: str, specs: str) -> str:
        """Generates a brief sales tip for a product."""
        prompt = f"""
        Eres un experto en ventas de tecnología para Claro. 
        Crea un "Tip de Venta" o "Speech" breve (máximo 20 palabras) para este producto:
        PRODUCTO: {model_name}
        ESPECIFICACIONES: {specs if specs else 'No disponibles'}
        
        El tip debe ser persuasivo, técnico pero fácil de entender, y resaltar un beneficio clave.
        Responde ÚNICAMENTE con el texto del tip, sin comillas ni introducciones.
        """
        
        try:
            if ai_pool:
                response = await ai_pool.generate(prompt)
                return response.strip()
        except Exception as e:
            print(f"Error AIService.generate_sales_tip: {e}")
            
        return "Destaca la excelente relación calidad-precio y la garantía de Claro."

    @staticmethod
    async def normalize_products_batch(descriptions: list) -> dict:
        """Normalizes product descriptions in batch."""
        if not descriptions or not ai_pool:
            return {}

        prompt = """
        Analiza esta lista de descripciones de productos tecnológicos.
        Para cada uno, extrae:
        - categoria: (TV, Celular, Laptop, Reloj, Audífonos, Parlante, Patineta, Tablet, Accesorio, Otro)
        - marca: La marca (Samsung, Huawei, etc.)
        - modelo_limpio: Nombre del modelo
        - especificaciones: Características clave
        - tip_venta: Un argumento de venta breve (máx 15 palabras) resaltando una ventaja técnica clave.
        Responde ÚNICAMENTE en JSON con las descripciones originales como llaves.
        LISTA: """ + json.dumps(descriptions)

        try:
            response_text = await ai_pool.generate(prompt)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except Exception as e:
            print(f"Error AIService.normalize_products_batch: {e}")
            
        return {}

ai_service = AIService()
