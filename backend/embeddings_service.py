import os
import json
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Constants
EMBEDDING_MODEL = "models/gemini-embedding-001"
STORAGE_DIR = "storage"
EMBEDDINGS_CACHE_FILE = os.path.join(STORAGE_DIR, "image_embeddings.json")

class EmbeddingsService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # Try secondary keys from ai_pool convention
            self.api_key = os.getenv("GEMINI_API_KEY_1")
            
        if not self.api_key:
            raise Exception("No GEMINI_API_KEY found in environment")
            
        genai.configure(api_key=self.api_key)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, List[float]]:
        if os.path.exists(EMBEDDINGS_CACHE_FILE):
            try:
                with open(EMBEDDINGS_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading embeddings cache: {e}")
        return {}

    def _save_cache(self):
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR)
        with open(EMBEDDINGS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def get_embedding(self, text: str) -> List[float]:
        """Fetch embedding from Gemini API."""
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error fetching embedding for '{text}': {e}")
            return []

    def get_image_embedding(self, filename: str, force_refresh: bool = False) -> List[float]:
        """Get embedding for a filename, using cache if available."""
        # Clean filename for better embedding (remove extension, replace separators)
        clean_name = filename.split('.')[0].replace('_', ' ').replace('-', ' ')
        
        if filename in self.cache and not force_refresh:
            return self.cache[filename]
            
        embedding = self.get_embedding(clean_name)
        if embedding:
            self.cache[filename] = embedding
            self._save_cache()
            
        return embedding

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not v1 or not v2:
            return 0.0
        
        a = np.array(v1)
        b = np.array(v2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(dot_product / (norm_a * norm_b))

    def find_best_match(self, product_name: str, available_filenames: List[str], threshold: float = 0.65) -> Optional[str]:
        """Find the best matching image filename for a product name."""
        if not available_filenames:
            return None
            
        # Get embedding for the product name
        product_vec = self.get_embedding(product_name.lower())
        if not product_vec:
            return None
            
        best_match = None
        max_score = -1.0
        
        for filename in available_filenames:
            img_vec = self.get_image_embedding(filename)
            if not img_vec:
                continue
                
            score = self.cosine_similarity(product_vec, img_vec)
            if score > max_score:
                max_score = score
                best_match = filename
                
        if max_score >= threshold:
            print(f"Semantic Match found: '{product_name}' -> '{best_match}' (score: {max_score:.4f})")
            return best_match
            
        return None

# Singleton instance
embeddings_service = EmbeddingsService()
