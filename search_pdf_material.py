import pdfplumber
import os

pdf_path = "backend/storage/Inventario 16-02-26 C230.pdf"

def search_material():
    target = "7023128"
    found = False
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and target in text:
                print(f"✅ Found {target} on page {i+1}")
                lines = text.split('\n')
                for line in lines:
                    if target in line:
                        print(f" Line: {line}")
                found = True
    if not found:
        print(f"❌ {target} not found in any page of the PDF.")

if __name__ == "__main__":
    search_material()
