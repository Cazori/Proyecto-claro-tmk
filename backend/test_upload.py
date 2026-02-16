import requests
import os

def test_upload():
    print("--- TEST DE SUBIDA DE ARCHIVO ---")
    url = "http://localhost:8000/upload-inventory"
    
    # Create a dummy PDF
    with open("dummy_inventory.pdf", "wb") as f:
        f.write(b"%PDF-1.4 dummy content")
    
    files = {"file": open("dummy_inventory.pdf", "rb")}
    
    try:
        print("Enviando archivo...")
        response = requests.post(url, files=files, timeout=5) # 5s timeout
        if response.status_code == 200:
            print(f"ÉXITO: {response.json()}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"FALLO DE CONEXIÓN: {e}")
    finally:
        files["file"].close()
        os.remove("dummy_inventory.pdf")

if __name__ == "__main__":
    test_upload()
