import pdfplumber
import os
import glob
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

def peek_hp():
    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if not files:
        print("No files found.")
        return
    
    latest_file = max(files, key=os.path.getmtime)
    print(f"Inspecting file: {latest_file}")
    
    with pdfplumber.open(latest_file) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if "HP" in line.upper() or "HEWP" in line.upper() or "7023197" in line:
                        print(f"RAW LINE: {line}")

if __name__ == "__main__":
    peek_hp()
