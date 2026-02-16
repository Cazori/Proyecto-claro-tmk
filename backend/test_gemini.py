import requests

def test_gemini_chat():
    url = "http://localhost:8000/chat"
    queries = [
        "¿Qué portátiles HP tenemos?",
        "¿Cuál es la diferencia entre la HP Ryzen 3 y la Ryzen 5?",
        "¿Tienes tablets con buena batería?"
    ]
    
    for q in queries:
        print(f"\nQUERY: {q}")
        try:
            response = requests.get(url, params={"query": q})
            data = response.json()
            print(f"CLEO: {data.get('response')}")
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_gemini_chat()
