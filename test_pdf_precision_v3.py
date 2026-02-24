import pdfplumber
import re
import os

pdf_path = "backend/storage/Inventario 16-02-26 C230.pdf"

# Current patterns from processor.py
pattern_strict = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?Aplica\s+\$.*?(\d[\d\.\s-]*(?:\d|$))"
pattern_flex = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?\$?\s?(\d{1,3}(?:\.\d{3})*(?:,\d+)?)"

def test_extraction():
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    potential_lines = []
    matches = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            lines = text.split('\n')
            for line in lines:
                # Look for the sequence: 7-8 digits followed immediately or with space by letters
                if re.search(r"\d{7,8}", line) and "Aplica $" in line:
                    potential_lines.append(line)
                    
                    found = False
                    # Check current regex
                    m = re.search(pattern_strict, line)
                    if not m:
                        m = re.search(pattern_flex, line)
                    
                    if m:
                        matches.append(line)

    print(f"--- Final Extraction Diagnostic ---")
    print(f"Total lines with ID and 'Aplica $': {len(potential_lines)}")
    print(f"Current Regex matched: {len(matches)}")
    if potential_lines:
        print(f"Success Rate: {(len(matches)/len(potential_lines))*100:.1f}%")
        
    print("\nSample of NON-MATCHING lines (why we are missing precision):")
    non_matches = [l for l in potential_lines if l not in matches]
    for l in non_matches[:15]:
        print(f" [FAIL] {l}")

if __name__ == "__main__":
    test_extraction()
