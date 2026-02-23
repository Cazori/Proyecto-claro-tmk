"""
Multi-Provider AI Pool System
Manages rotation between multiple AI providers with automatic fallback and performance tracking.
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
import httpx

# Provider SDKs (will be imported conditionally)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = False  # Will enable when user provides key
except ImportError:
    ANTHROPIC_AVAILABLE = False


class RotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    FASTEST_FIRST = "fastest"
    FALLBACK = "fallback"


class AIProvider:
    """Base class for AI providers"""
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_latency_ms": 0,
            "avg_latency_ms": 0,
            "last_error": None,
            "last_used": None
        }
    
    async def generate(self, prompt: str) -> str:
        """Generate response from AI provider"""
        raise NotImplementedError
    
    def update_stats(self, success: bool, latency_ms: float, error: Optional[str] = None):
        """Update provider statistics"""
        self.stats["total_requests"] += 1
        self.stats["last_used"] = datetime.now().isoformat()
        
        if success:
            self.stats["successful"] += 1
            self.stats["total_latency_ms"] += latency_ms
            self.stats["avg_latency_ms"] = self.stats["total_latency_ms"] / self.stats["successful"]
        else:
            self.stats["failed"] += 1
            self.stats["last_error"] = error


class GeminiProvider(AIProvider):
    """Google Gemini provider"""
    def __init__(self, name: str, api_key: str, model: str = "models/gemini-flash-latest"):
        super().__init__(name, api_key)
        self.model_name = model
        if GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
        else:
            raise ImportError("google-generativeai not installed")
    
    async def generate(self, prompt: str) -> str:
        start_time = time.time()
        try:
            response = await self.model.generate_content_async(prompt)
            latency_ms = (time.time() - start_time) * 1000
            
            if hasattr(response, 'text') and response.text:
                self.update_stats(True, latency_ms)
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.update_stats(False, latency_ms, error_msg)
            raise Exception(f"Gemini error: {error_msg}")


class GroqProvider(AIProvider):
    """Groq provider (ultra-fast inference)"""
    def __init__(self, name: str, api_key: str, model: str = "llama-3.3-70b-versatile"):
        super().__init__(name, api_key)
        self.model_name = model
        self.base_url = "https://api.groq.com/openai/v1"
    
    async def generate(self, prompt: str) -> str:
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Some models prefer a system message + user message
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "Eres Cleo, un asistente útil para inventarios."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 1024
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception(f"Groq API Error {response.status_code}: {error_detail}")
                
                data = response.json()
                
                latency_ms = (time.time() - start_time) * 1000
                text = data["choices"][0]["message"]["content"]
                self.update_stats(True, latency_ms)
                return text.strip()
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.update_stats(False, latency_ms, error_msg)
            raise Exception(f"Groq error: {error_msg}")


class GrokProvider(AIProvider):
    """xAI Grok provider"""
    def __init__(self, name: str, api_key: str, model: str = "grok-beta"):
        super().__init__(name, api_key)
        self.model_name = model
        self.base_url = "https://api.x.ai/v1"
    
    async def generate(self, prompt: str) -> str:
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                latency_ms = (time.time() - start_time) * 1000
                text = data["choices"][0]["message"]["content"]
                self.update_stats(True, latency_ms)
                return text.strip()
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.update_stats(False, latency_ms, error_msg)
            raise Exception(f"Grok error: {error_msg}")


class OpenAIProvider(AIProvider):
    """OpenAI provider"""
    def __init__(self, name: str, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(name, api_key)
        self.model_name = model
        if OPENAI_AVAILABLE:
            self.client = openai.AsyncOpenAI(api_key=api_key)
        else:
            raise ImportError("openai not installed")
    
    async def generate(self, prompt: str) -> str:
        start_time = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            latency_ms = (time.time() - start_time) * 1000
            text = response.choices[0].message.content
            self.update_stats(True, latency_ms)
            return text.strip()
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self.update_stats(False, latency_ms, error_msg)
            raise Exception(f"OpenAI error: {error_msg}")


class AIPool:
    """Manages multiple AI providers with automatic rotation and fallback"""
    
    def __init__(self, strategy: RotationStrategy = RotationStrategy.FALLBACK):
        self.providers: List[AIProvider] = []
        self.strategy = strategy
        self.current_index = 0
        self.stats_file = "performance_tracker.json"
        self._quota_blacklist: set = set()  # Providers with 429 in current request cycle
        
        # Load providers from environment
        self._load_providers()
        
        # Load historical stats
        self._load_stats()
    
    def _load_providers(self):
        """Load AI providers from environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Gemini providers (multiple keys supported)
        gemini_keys = []
        for i in range(1, 10):  # Support up to 9 Gemini keys
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                gemini_keys.append(key)
        
        # Fallback to single GEMINI_API_KEY
        if not gemini_keys:
            key = os.getenv("GEMINI_API_KEY")
            if key:
                gemini_keys.append(key)
        
        # Add Gemini providers
        for idx, key in enumerate(gemini_keys, 1):
            try:
                provider = GeminiProvider(f"gemini-{idx}", key)
                self.providers.append(provider)
                print(f"✓ Loaded Gemini provider #{idx}")
            except Exception as e:
                print(f"✗ Failed to load Gemini #{idx}: {e}")
        
        # Groq providers (multiple keys supported - ultra-fast)
        groq_keys = []
        for i in range(1, 10):  # Support up to 9 Groq keys
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key:
                groq_keys.append(key)
        
        # Fallback to single GROQ_API_KEY
        if not groq_keys:
            key = os.getenv("GROQ_API_KEY")
            if key:
                groq_keys.append(key)
        
        # Add Groq providers
        for idx, key in enumerate(groq_keys, 1):
            try:
                provider = GroqProvider(f"groq-{idx}", key)
                self.providers.append(provider)
                print(f"✓ Loaded Groq provider #{idx} (ultra-fast)")
            except Exception as e:
                print(f"✗ Failed to load Groq #{idx}: {e}")
        
        # Grok provider
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            try:
                provider = GrokProvider("grok-beta", grok_key)
                self.providers.append(provider)
                print(f"✓ Loaded Grok provider")
            except Exception as e:
                print(f"✗ Failed to load Grok: {e}")
        
        # OpenAI provider
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and OPENAI_AVAILABLE:
            try:
                provider = OpenAIProvider("openai-mini", openai_key)
                self.providers.append(provider)
                print(f"✓ Loaded OpenAI provider")
            except Exception as e:
                print(f"✗ Failed to load OpenAI: {e}")
        
        if not self.providers:
            raise Exception("No AI providers configured! Please add API keys to .env")
        
        print(f"\n🎯 AI Pool initialized with {len(self.providers)} provider(s)")
    
    def _load_stats(self):
        """Load historical performance stats"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    historical_stats = json.load(f)
                    
                # Merge historical stats with current providers
                for provider in self.providers:
                    if provider.name in historical_stats:
                        provider.stats.update(historical_stats[provider.name])
        except Exception as e:
            print(f"Warning: Could not load stats: {e}")
    
    def _save_stats(self):
        """Save performance stats to file"""
        try:
            stats_dict = {p.name: p.stats for p in self.providers}
            with open(self.stats_file, 'w') as f:
                json.dump(stats_dict, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save stats: {e}")
    
    def _get_next_provider(self, exclude: set = None) -> AIProvider:
        """Get next provider based on rotation strategy, skipping excluded ones."""
        excluded = exclude or set()
        available = [p for p in self.providers if p.name not in excluded]
        if not available:
            return None

        if self.strategy == RotationStrategy.ROUND_ROBIN:
            # Pick next available provider in circular order
            for _ in range(len(self.providers)):
                provider = self.providers[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.providers)
                if provider.name not in excluded:
                    return provider
            return available[0]

        elif self.strategy == RotationStrategy.FASTEST_FIRST:
            # Sort by average latency; providers with no success go last
            sorted_providers = sorted(
                available,
                key=lambda p: p.stats["avg_latency_ms"] if p.stats["successful"] > 0 else float('inf')
            )
            return sorted_providers[0]

        else:  # FALLBACK — try in list order, skipping excluded
            return available[0]
    
    async def generate(self, prompt: str, max_retries: int = None) -> str:
        """
        Generate response using AI pool with automatic fallback.
        Tries each provider at most once per call; skips providers on 429.
        """
        if max_retries is None:
            max_retries = len(self.providers)
        
        last_error = None
        tried: set = set()  # Track providers tried in this call

        while len(tried) < len(self.providers):
            provider = self._get_next_provider(exclude=tried)
            if provider is None:
                break

            tried.add(provider.name)
            
            try:
                print(f"🤖 Trying {provider.name}...")
                response = await provider.generate(prompt)
                self._save_stats()
                return response
                
            except Exception as e:
                last_error = str(e)
                print(f"⚠️  {provider.name} failed: {last_error}")
                # Always continue to next provider regardless of error type
                continue
        
        # All providers failed
        self._save_stats()
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all providers"""
        return {
            "providers": [
                {
                    "name": p.name,
                    "stats": p.stats
                }
                for p in self.providers
            ],
            "strategy": self.strategy.value,
            "total_providers": len(self.providers)
        }
