
import sys
import os
import json
import pandas as pd
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.inventory_service import inventory_service

async def test_context():
    df = await inventory_service.get_latest_inventory_df()
    if df is not None and not df.empty:
        # Pick a sample product
        sample = df.head(1)
        print(f"Testing for Material: {sample.iloc[0]['Material']}")
        context = inventory_service.format_inventory_context(sample)
        print("--- CONTEXT OUTPUT ---")
        print(context)
        print("----------------------")
        if "CUOTAS:" in context and "N/A" not in context:
            print("✅ SUCCESS: Quotas found in context.")
        else:
            print("⚠️ WARNING: Quotas might be N/A if mapping is missing for this specific ID.")
    else:
        print("❌ No inventory found.")

if __name__ == "__main__":
    asyncio.run(test_context())
