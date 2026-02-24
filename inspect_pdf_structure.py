import pdfplumber
import os

pdf_path = "backend/storage/Inventario 16-02-26 C230.pdf"

def inspect_pdf():
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    with pdfplumber.open(pdf_path) as pdf:
        # Check first page
        page = pdf.pages[0]
        text = page.extract_text()
        print(f"--- Raw Text Samples (Page 1) ---")
        if text:
            lines = text.split('\n')
            for i, line in enumerate(lines[:50]):
                print(f"{i:02d}: {list(line[:100]) if i < 5 else line[:100]}") # Show chars for first few to see spaces/tabs
        else:
            print("No text found on page 1.")

if __name__ == "__main__":
    inspect_pdf()
