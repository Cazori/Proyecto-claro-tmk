import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_1")
genai.configure(api_key=api_key)

print("--- Modelos Disponibles para Embeddings ---")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"ID: {m.name}")
        print(f"Display Name: {m.display_name}")
        print(f"Description: {m.description}")
        print("-" * 30)
