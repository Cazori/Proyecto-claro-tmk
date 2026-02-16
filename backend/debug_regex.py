import re
import pdfplumber
import os
import glob

STORAGE_DIR = "storage"

def debug_regex():
    files = glob.glob(os.path.join(STORAGE_DIR, "*.pdf"))
    if not files: return
    latest_file = max(files, key=os.path.getmtime)
    
    with pdfplumber.open(latest_file) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        clean_text = text.replace('\n', ' ')
        
        print("\n--- EXPERIMENTAL REGEX TESTS ---")
        # Pattern 3: Handle no-space category and greedy description
        # (\d{7}) Material
        # (.*?) Description
        # (\d+) Stock
        # \s*(\d*) Comprometido
        # ([A-Z]{3,}) Category
        test_pattern = r"(\d{7})\s*(.*?)\s+(\d+)\s*(\d*)\s*([A-Z]{3,})"
        
        for i, match in enumerate(re.finditer(test_pattern, clean_text)):
            end_pos = match.end()
            context = clean_text[end_pos:end_pos+100]
            print(f"MATCH {i}: Mat={match.group(1)} | Desc={match.group(2)[:30]} | Stock={match.group(3)} | Cat={match.group(5)}")
            print(f"   CONTEXT: {context}")
            if i > 5: break # Just a few

if __name__ == "__main__":
    debug_regex()
