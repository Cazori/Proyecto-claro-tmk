import pdfplumber
import re
import os

pdf_path = "backend/storage/Inventario 16-02-26 C230.pdf"

# Current patterns
pattern_strict = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?Aplica\s+\$.*?(\d[\d\.\s-]*(?:\d|$))"
pattern_flex = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?\$?\s?(\d{1,3}(?:\.\d{3})*(?:,\d+)?)"

def test_extraction():
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    total_potential_items = 0
    matched_items = 0
    failed_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text: continue
            
            lines = text.split('\n')
            for line in lines:
                # Does it look like a product line? (Contains a 7-digit ID and 'Aplica $')
                if re.search(r"\b\d{7,8}\b", line) and "Aplica $" in line:
                    total_potential_items += 1
                    
                    match = re.search(pattern_strict, line)
                    if not match:
                        match = re.search(pattern_flex, line)
                    
                    if match:
                        matched_items += 1
                    else:
                        failed_lines.append(line)

    print(f"--- Extraction Diagnostic (Full PDF) ---")
    print(f"Potential items found (ID + 'Aplica $'): {total_potential_items}")
    print(f"Matched by current regex: {matched_items}")
    if total_potential_items > 0:
        print(f"Success rate: {(matched_items/total_potential_items)*100:.1f}%")
    
    if failed_lines:
        print(f"\nSample failed lines (First 20):")
        for line in failed_lines[:20]:
            print(f" [FAIL] {line}")

if __name__ == "__main__":
    test_extraction()
