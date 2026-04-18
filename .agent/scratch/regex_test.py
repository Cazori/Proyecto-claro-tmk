import re

lines = [
    "CEM Bogotá - ZF C230 H001 7018525MINICOMPTE AKX110 300W RADIO FM MP3 PNSC 9 0MINICOMPONENATpElica $ - $ 534.900 $ 534.900",
    "CEM Bogotá - ZF C230 H001 7020163KCK SCTER E2PLUS NINEBOT 500WH GRIS SGWY 1 0PATINETA Aplica $ - $ 1 .822.900 $ 1 .822.900",
    "CEM Bogotá - ZF C230 H001 7023048PORT B1503CVA-S75191W ICI3 15.6\" NG ASUS 9 0PORTATIL Aplica $ - $ 2 .553.900 $ 2 .553.900",
    "CEM Cali C431 H001 7021695SMRTWTCH GT5PRO 1.43\" B5.2 323M NGR HUAW 1 0SMARTWATCHAplica $ - $ 949.900 $ 949.900"
]

pattern_v3 = r"(\d{7,8})\s*(.+?)\s+(\d+)\s+(\d+).*?([A-Za-z]+)\s*Aplica\s+\$(.*)"
# Let's see if we can capture the category correctly
for line in lines:
    match = re.search(pattern_v3, line, re.IGNORECASE)
    if match:
        print(f"Subproducto: {match.group(2)} | Categoria: {match.group(5).strip().upper()}")
    else:
        print(f"Skipped: {line}")
