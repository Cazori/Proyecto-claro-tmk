import pandas as pd
import os

QUOTAS_EXCEL = "storage/cuotas.xlsx"

def inspect_excel():
    if not os.path.exists(QUOTAS_EXCEL):
        print("File not found")
        return
        
    xl = pd.ExcelFile(QUOTAS_EXCEL)
    print(f"Sheets: {xl.sheet_names}")
    
    # Check first sheet
    df = pd.read_excel(QUOTAS_EXCEL, sheet_name=xl.sheet_names[0], header=None).head(20)
    print("\n--- FIRST 20 ROWS OF SHEET 1 ---")
    print(df.to_string())
    
    # Check second sheet if it exists
    if len(xl.sheet_names) > 1:
        df2 = pd.read_excel(QUOTAS_EXCEL, sheet_name=xl.sheet_names[1], header=None).head(20)
        print("\n--- FIRST 20 ROWS OF SHEET 2 ---")
        print(df2.to_string())

if __name__ == "__main__":
    inspect_excel()
