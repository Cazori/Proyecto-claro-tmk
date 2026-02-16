import requests
import json
import time

def test_chat():
    print("--- TEST CHAT ENDPOINT (VIA HTTP) ---")
    queries = [
        "televisores samsung",
        "audifonos",
        "patineta"
    ]
    
    for q in queries:
        print(f"\nConsulta: '{q}'")
        try:
            start = time.time()
            res = requests.get(f"http://localhost:8000/chat?query={q}", timeout=10)
            dur = time.time() - start
            if res.status_code == 200:
                data = res.json()
                print(f"Status: 200 OK (Tiempo: {dur:.2f}s)")
                print(f"Respuesta: {str(data)[:100]}...")
            else:
                print(f"Status: {res.status_code}")
                print(res.text)
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_chat()
