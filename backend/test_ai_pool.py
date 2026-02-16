"""
Test script for AI Pool functionality
"""

import asyncio
from ai_pool import AIPool, RotationStrategy

async def test_pool():
    print("=== Testing AI Pool ===\n")
    
    # Initialize pool
    pool = AIPool(strategy=RotationStrategy.FALLBACK)
    
    # Test prompt
    test_prompt = """
    Eres Cleo, asistente de inventario. 
    
    CONTEXTO DE INVENTARIO:
    - PRODUCTO: PRT HEWP 15-FD0XXX | BODEGA: Bogotá - ZF | STOCK: 5 | PRECIO: $1,200,000 | ES_BOGOTA: True
    - PRODUCTO: PRT HEWP 14-DQ0XXX | BODEGA: Bogotá - ZF | STOCK: 3 | PRECIO: $950,000 | ES_BOGOTA: True
    
    PREGUNTA: "¿Qué portátiles HP tenemos?"
    
    Responde en formato tabla markdown.
    """
    
    try:
        print("🤖 Generating response...\n")
        response = await pool.generate(test_prompt)
        print("✅ Response received:\n")
        print(response)
        print("\n" + "="*50)
        
        # Show stats
        stats = pool.get_stats()
        print("\n📊 Performance Stats:")
        for provider_info in stats["providers"]:
            name = provider_info["name"]
            pstats = provider_info["stats"]
            print(f"\n{name}:")
            print(f"  Total requests: {pstats['total_requests']}")
            print(f"  Success rate: {pstats['successful']}/{pstats['total_requests']}")
            if pstats['successful'] > 0:
                print(f"  Avg latency: {pstats['avg_latency_ms']:.0f}ms")
            if pstats['last_error']:
                print(f"  Last error: {pstats['last_error'][:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pool())
