
import sys
import os
import json
import pandas as pd

# Add current dir to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils import resolve_spec_match
from config import SPECS_DIR, SPECS_MAPPING_FILE

def test_resolve():
    print("--- Diagnostic Spec Resolution ---")
    
    available_specs = os.listdir(SPECS_DIR) if os.path.exists(SPECS_DIR) else []
    
    manual_map = {}
    if os.path.exists(SPECS_MAPPING_FILE):
        with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
            manual_map = json.load(f)
            
    print(f"Manual Map size: {len(manual_map)}")
    
    test_cases = [
        {"id": "7023238", "name": "SMRTWTCH WGT6PRO 46MM BLTH6.0 NEGRO HUAW"},
        {"id": "7023239", "name": "SMRTWTCH WGT6 41MM BLT6.0 540MH PRP HUAW"},
        {"id": "7023242", "name": "SMRTWTCH WGT6 41MM BLTH6.0 540MH NG HUAW"}
    ]
    
    for case in test_cases:
        res = resolve_spec_match(case['id'], case['name'], available_specs, manual_map)
        print(f"ID: {case['id']} | Name: {case['name']}")
        print(f"  => Result: {res}")
        print("-" * 20)

if __name__ == "__main__":
    test_resolve()
