import json
import math

data = json.load(open('backend/storage/quota_mapping.json', encoding='utf-8'))

# Tomamos los productos con mas plazos para analizar
samples = [(k, v) for k, v in data.items() if len(v) >= 4][:6]

print("=" * 65)
print("ANALISIS DE CUOTAS - Buscando tasa de interes mensual")
print("=" * 65)

# Formula de amortizacion francesa:
# cuota = P * i / (1 - (1+i)^-n)
# Donde: P = precio, i = tasa mensual, n = numero de cuotas

def calcular_tasa(precio, cuota, n):
    """Busca la tasa mensual por biseccion"""
    lo, hi = 0.0001, 0.10
    for _ in range(1000):
        mid = (lo + hi) / 2
        c = precio * mid / (1 - (1 + mid)**-n)
        if abs(c - cuota) < 0.5:
            return mid
        elif c < cuota:
            lo = mid
        else:
            hi = mid
    return mid

# Para esto necesito el precio de contado de cada producto
# Lo busco en processed_inventory.json
inv = json.load(open('backend/storage/processed_inventory.json', encoding='utf-8'))
inv_map = {str(item['Material']): item.get('Precio Contado', 0) for item in inv}

tasas = []
for mat, plans in samples:
    precio = inv_map.get(mat, 0)
    if not precio:
        continue
    print(f"\nMaterial: {mat} | Precio contado: ${precio:,.0f}")
    for months, cuota in sorted(plans.items(), key=lambda x: int(x[0])):
        n = int(months)
        tasa = calcular_tasa(precio, cuota, n)
        tasa_anual = tasa * 12 * 100
        total_pago = cuota * n
        interes_total = total_pago - precio
        print(f"  {n:2d} meses: cuota=${cuota:,} | tasa mens={tasa*100:.3f}% | tasa anual={tasa_anual:.2f}% | total=${total_pago:,.0f} | interes=${interes_total:,.0f}")
        tasas.append(tasa)

# Promedio de tasas
if tasas:
    avg = sum(tasas) / len(tasas)
    print(f"\n{'='*65}")
    print(f"TASA MENSUAL PROMEDIO: {avg*100:.4f}%")
    print(f"TASA ANUAL PROMEDIO:   {avg*12*100:.2f}%")

    # Calcular cuotas para un valor de 2,613,000
    P = 2613000
    print(f"\n{'='*65}")
    print(f"CALCULO PARA PRECIO: ${P:,}")
    print(f"{'='*65}")
    for n in [6, 12, 18, 24, 36]:
        cuota = P * avg / (1 - (1 + avg)**-n)
        total = cuota * n
        interes = total - P
        print(f"  {n:2d} cuotas: ${cuota:,.0f}/mes | Total: ${total:,.0f} | Interes: ${interes:,.0f}")
