import re

test_lines = [
    "CEM Bogotá - ZF C230 H001 7022803AUDIFONS OWS LOKY BLTTH5.2 IP54 NGR HONR 2 0AUDIFONOS Aplica $ - $",
    "CEM Bogotá - ZF C230 H001 7022393CAMARA EPIC88 4K 24MP 128G IP68 NGR ARGM 10 0CAMARA Aplica $ - $ 59",
    "CEM Bogotá - ZF C230 H001 7023333CS PS5 SLM_DGT 825G+VJ ASTRB+VJ GT7 SONY 92 0CONSOLA Aplica $ 554.6",
    "CEM Barranquilla C630 H001 7021504CNS XBOX S/S 512G+2CNTRLS+GIFT CARD MSFT 1 0CONSOLA Aplica $ 460.4",
    "CEM Medellin C433 H001 7022501AUDF FREECLIP 20W BLTTH5.2 510MH NG HUAW 2 0AUDIFONOS Aplica $ - $ 549",
    "CEM Bogotá - ZF C230 H001 7020163KCK SCTER E2PLUS NINEBOT 500WH GRIS SGWY 1 0PATINETA Aplica $ - $ 1"
]

pattern_v3 = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?Aplica\s+\$(.*)"

for line in test_lines:
    print(f"\nLine: {line}")
    m = re.search(pattern_v3, line)
    if m:
        material, name, total, disp, tail = m.groups()
        # Find all number sequences (including single digits)
        prices = re.findall(r"(\d[\d\.\s,]*\d|\d)", tail)
        if prices:
            price_val = prices[-1] # Take the last one
        else:
            price_val = "-" if "-" in tail else "0"
            
        print(f"  Found: ID={material}, Name={name}, Price={price_val}")
    else:
        print("  FAIL")
