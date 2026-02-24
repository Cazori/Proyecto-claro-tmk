import asyncio
import pandas as pd
from processor import process_inventory_pdf
import os

pdf_path = "storage/Inventario 16-02-26 C230.pdf"

async def verify():
    print("🚀 Running Verification Census...")
    df = await process_inventory_pdf(pdf_path)
    if df is not None:
        print(f"\n✅ Final Result: {len(df)} items indexed for Bogotá.")
        print("\nSample of items with $0 price (hyphenated in PDF):")
        zeros = df[df["Precio Contado"] == 0]
        print(zeros[["Material", "Subproducto", "CantDisponible"]].head(10))
    else:
        print("❌ Error: No items extracted.")

if __name__ == "__main__":
    asyncio.run(verify())
