import requests
try:
    r = requests.get('http://localhost:8000/chat', params={'query': 'que portatiles tenemos'})
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
