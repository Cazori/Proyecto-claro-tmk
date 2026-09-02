import os
import json
import pandas as pd
from config import STORAGE_DIR, SPECS_DIR, KNOWLEDGE_FILE, SPECS_MAPPING_FILE, QUOTA_MAPPING_FILE
from utils import normalize_str, resolve_spec_match, log_debug

class InventoryService:
    @staticmethod
    async def get_latest_inventory_df():
        """
        Retrieves the latest inventory DataFrame.
        Imported here to avoid circular dependencies with processor.py if needed,
        though better to refactor processor.py to use this.
        """
        from processor import get_latest_inventory
        return await get_latest_inventory()

    @staticmethod
    def filter_inventory(df: pd.DataFrame, valid_keywords: list) -> pd.DataFrame:
        """Filters the inventory based on keywords."""
        if not valid_keywords:
            return pd.DataFrame()

        # Category aliases so short keywords can match full category names
        CATEGORIA_ALIASES = {
            "tv": ["televisor", "television"],
            "prt": ["portatil", "laptop", "port", "notebook"],
            "tab": ["tablet"],
            "cel": ["celular", "telefono", "smartphone"],
            "reloj": ["smartwatch", "watch"],
            "sw": ["smartwatch", "watch"],
            "ptn": ["patineta", "scooter"],
            "aud": ["audifonos", "auriculares", "cascos"],
        }

        def _matches_categoria(k, categoria_norm):
            """Check if keyword matches category field with alias expansion."""
            if k in categoria_norm:
                return True
            for alias in CATEGORIA_ALIASES.get(k, []):
                if alias in categoria_norm or categoria_norm in alias:
                    return True
            return False

        def matches_keywords(row):
            categoria_norm = normalize_str(row.get("categoria", ""))
            for k in valid_keywords:
                if '\"' in k:
                    if k not in normalize_str(row["Subproducto"]): return False
                elif not (k in normalize_str(row["Subproducto"]) or 
                         k in normalize_str(row["Material"]) or 
                         k in normalize_str(row["modelo_limpio"]) or
                         k in normalize_str(row["especificaciones"]) or
                         _matches_categoria(k, categoria_norm) or
                         (k == "ptn" and any(s in normalize_str(row["Subproducto"]) for s in ["ptn", "ptnet", "patinet", "scter"]))):
                    return False
            return True
        
        mask = df.apply(matches_keywords, axis=1)
        return df[mask]

    @staticmethod
    def apply_intent_filters(df: pd.DataFrame, intent: dict) -> pd.DataFrame:
        """Applies filters based on AI-analyzed intent."""
        results = df.copy()
        
        if intent.get("categoria"):
            cat_raw = intent["categoria"].lower()
            
            def matches_category(row):
                item_cat = normalize_str(row["categoria"])
                # Búsqueda exacta o contenida sobre la categoría oficial
                return cat_raw in item_cat or item_cat in cat_raw
            
            results = results[results.apply(matches_category, axis=1)]
            log_debug(f"AI PATH: After Categoria ({cat_raw}): {len(results)}")

        if intent.get("marca") and not results.empty:
            brand_filter = intent["marca"].lower()
            results = results[results["marca"].apply(lambda x: brand_filter in normalize_str(x) or normalize_str(x) in brand_filter)]
            log_debug(f"AI PATH: After Marca ({brand_filter}): {len(results)}")

        if intent.get("modelo") and not results.empty:
            mod_raw = normalize_str(intent["modelo"]).replace("pulgadas", "\"").replace("pulgada", "\"").replace("pulgs", "\"")
            mod_keywords = [w for w in mod_raw.split() if len(w) > 1 and w != "\""]
            if mod_keywords:
                mask = results.apply(lambda row: 
                                     all(k in normalize_str(row["Subproducto"]) or 
                                         k in normalize_str(row["Material"]) or
                                         k in normalize_str(row["modelo_limpio"]) or
                                         k in normalize_str(row["marca"]) or # Added brand to model too
                                         k in normalize_str(row["especificaciones"]) for k in mod_keywords), axis=1)
                results = results[mask]
        
        log_debug(f"AI PATH: Final results: {len(results)}")
        return results

    @staticmethod
    def _build_inventory_rows(results: pd.DataFrame) -> list:
        """Builds a list of dicts with all display fields for each inventory item.

        Shared by the text context and the deterministic Markdown renderer so the
        formatting logic (specs, images, quotas, sales tips) lives in one place.
        """
        try:
            available_specs = os.listdir(SPECS_DIR)
            with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
                manual_map = json.load(f)
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                expert_data = json.load(f)
                expert_tips = {item['sku']: item.get('tip_venta') for item in expert_data if item.get('tip_venta')}

            quotas_map = {}
            if os.path.exists(QUOTA_MAPPING_FILE):
                with open(QUOTA_MAPPING_FILE, "r", encoding="utf-8") as f:
                    quotas_map = json.load(f)
        except Exception:
            available_specs, manual_map, expert_tips, quotas_map = [], {}, {}, {}

        # Sort and limit
        results = results.sort_values(by=["CantDisponible"], ascending=False)
        results = results.drop_duplicates(subset=["Material"], keep="first")

        # Ensure 'Precio Cuotas' column exists defensively to prevent KeyErrors
        if "Precio Cuotas" not in results.columns:
            if "Precio Contado" in results.columns:
                results["Precio Cuotas"] = results["Precio Contado"]
            else:
                results["Precio Cuotas"] = 0.0

        results = results.sort_values(by=["CantDisponible", "Precio Cuotas"], ascending=[False, False]).head(500)

        rows = []
        for _, item in results.iterrows():
            match = resolve_spec_match(item['Material'], item['Subproducto'], available_specs, manual_map)
            has_image = "NO"
            if match and isinstance(match, str):
                if any(match.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    has_image = "SI"

            ficha_tag = "SI" if match else "NO"
            try:
                raw_price = item.get('Precio Cuotas', 0)
                precio = f"${float(raw_price):,.0f}" if pd.notnull(raw_price) and str(raw_price).replace('.', '', 1).isdigit() else str(raw_price)
            except Exception:
                precio = str(item.get('Precio Cuotas', '-'))

            sku_str = str(item['Material'])
            final_tip = expert_tips.get(sku_str, item.get('tip_venta', '-'))
            if not final_tip or final_tip == "nan" or pd.isna(final_tip):
                final_tip = "-"

            try:
                stock_val = int(float(item.get('CantDisponible', 0)))
            except Exception:
                stock_val = 0

            # Get quotas for this material
            mat_id_str = str(item['Material'])
            item_quotas = quotas_map.get(mat_id_str) or quotas_map.get(mat_id_str.strip().lstrip('0'))
            quotas_info = "N/A"
            if item_quotas:
                quotas_info = ", ".join([f"{m}m: ${val:,.0f}" for m, val in item_quotas.items()])

            rows.append({
                "referencia": str(item['Material']),
                "ficha": ficha_tag,
                "imagen": "VER" if has_image == "SI" else "-",
                "marca": item.get('marca', 'N/A'),
                "modelo": item['Subproducto'],
                "precio": precio,
                "unidades": str(stock_val),
                "caracteristicas": str(item.get('especificaciones', '-')),
                "tip": final_tip,
                "cuotas": quotas_info,
                "categoria": item.get('categoria', ''),
            })
        return rows

    @staticmethod
    def format_inventory_context(results: pd.DataFrame) -> str:
        """Formats the filtered inventory results into a human-readable string for the AI prompt."""
        if results.empty:
            return "No se encontraron productos que coincidan exactamente con la búsqueda."

        rows = InventoryService._build_inventory_rows(results)
        if not rows:
            return "No se encontraron productos que coincidan exactamente con la búsqueda."

        inventory_context = ""
        for r in rows:
            line = f"- [ID: {r['referencia']}] MODELO: {r['modelo']} | FICHA: {r['ficha']} | IMG: {r['imagen']} | CATEGORIA: {r['categoria']} | MARCA: {r['marca']} | DESC: {r['caracteristicas']} | STOCK: {r['unidades']} | PRECIO CUOTAS: {r['precio']} | CUOTAS: {r['cuotas']} | TIP: {r['tip']}\n"
            inventory_context += line

        return inventory_context

    EMPTY_RESPONSE = "No encontré equipos con esa descripción en Bogotá. ¿Deseas buscar otra categoría?"

    @staticmethod
    def render_inventory_markdown(results: pd.DataFrame) -> str:
        """Deterministically renders inventory results as a Markdown table (no AI).

        This replaces the LLM-based `generate_response` for the result table. It is
        exact, predictable, and cannot hallucinate prices or break the 1-to-1 rule.
        """
        if results.empty:
            return InventoryService.EMPTY_RESPONSE

        rows = InventoryService._build_inventory_rows(results)
        if not rows:
            return InventoryService.EMPTY_RESPONSE

        header = "| Referencia | Ficha | Imagen | Marca | Modelo | Precio | Unidades | Caracteristicas | Tip |"
        separator = "|---|---|---|---|---|---|---|---|---|"

        def esc(cell: str) -> str:
            # Escape pipe and newlines so they don't break the Markdown table
            return str(cell).replace("|", "/").replace("\n", " ").replace("\r", " ").strip()

        lines = [header, separator]
        for r in rows:
            tip_col = r['tip'] if r['tip'] and r['tip'] != "-" else "-"
            lines.append(
                f"| {esc(r['referencia'])} | {r['ficha']} | {r['imagen']} | {esc(r['marca'])} | "
                f"{esc(r['modelo'])} | {esc(r['precio'])} | {r['unidades']} | {esc(r['caracteristicas'])} | {esc(tip_col)} |"
            )
        return "\n".join(lines)

inventory_service = InventoryService()
