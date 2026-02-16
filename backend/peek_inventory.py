import pdfplumber
import os
import glob
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

def peek_pdf():
    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if not files:
        print("No files found.")
        return
    
    latest_file = max(files, key=os.path.getmtime)
    print(f"Peeking into: {latest_file}")
    
    with pdfplumber.open(latest_file) as pdf:
        # Just the first page for inspection
        text = pdf.pages[0].extract_text()
        print("---------------- RAW TEXT START ----------------")
        print(text[:2000] if text else "EMPTY TEXT")
        print("---------------- RAW TEXT END ----------------")

if __name__ == "__main__":
    peek_pdf()
