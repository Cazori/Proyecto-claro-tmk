import pdfplumber
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

def dump_inventory():
    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if not files: return
    latest_file = max(files, key=os.path.getmtime)
    
    with pdfplumber.open(latest_file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                print(f"--- PAGE {i+1} ---")
                # Print everything for the first few pages to see header/pattern
                if i < 2:
                    print(text)
                else:
                    # Just search for HP in later pages
                    for line in text.split("\n"):
                        if "HP" in line.upper() or "HEWP" in line.upper():
                            print(line)

if __name__ == "__main__":
    dump_inventory()
