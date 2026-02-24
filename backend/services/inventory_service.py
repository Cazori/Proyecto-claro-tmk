import os
import json
import pandas as pd
from config import STORAGE_DIR, SPECS_DIR, KNOWLEDGE_FILE, SPECS_MAPPING_FILE
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

        def matches_keywords(row):
            for k in valid_keywords:
                if '\"' in k:
                    if k not in normalize_str(row["Subproducto"]): return False
                elif not (k in normalize_str(row["Subproducto"]) or 
                         k in normalize_str(row["Material"]) or 
                         k in normalize_str(row["modelo_limpio"]) or
                         k in normalize_str(row["especificaciones"]) or
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
            cat_filter = intent["categoria"].lower()
            def matches_category(row):
                item_cat = normalize_str(row["categoria"])
                item_name = normalize_str(row["Subproducto"])
                if cat_filter in item_cat or item_cat in cat_filter: return True
                if item_cat in ["n/a", "otro", "", "none"]:
                    synonyms = [cat_filter]
                    if cat_filter == "tv": synonyms.extend(["tv", "televis", "smart"])
                    if cat_filter == "audífonos": synonyms.extend(["aud", "auric", "buds"])
                    if cat_filter == "celular": synonyms.extend(["cel", "tel", "phone", "iphone", "galaxy"])
                    if cat_filter == "tablet": synonyms.extend(["tablet", "tab", "ipad"])
                    if cat_filter == "patineta": synonyms.extend(["patine", "ptnta", "ptneta", "scter", "scooter"])
                    return any(s in item_name for s in synonyms)
                return False
            results = results[results.apply(matches_category, axis=1)]

        if intent.get("marca") and not results.empty:
            brand_filter = intent["marca"].lower()
            results = results[results["marca"].apply(lambda x: brand_filter in normalize_str(x) or normalize_str(x) in brand_filter)]

        if intent.get("modelo") and not results.empty:
            mod_raw = normalize_str(intent["modelo"]).replace("pulgadas", "\"").replace("pulgada", "\"").replace("pulgs", "\"")
            mod_keywords = [w for w in mod_raw.split() if len(w) > 1 and w != "\""]
            if mod_keywords:
                mask = results.apply(lambda row: 
                                     all(k in normalize_str(row["Subproducto"]) or 
                                         k in normalize_str(row["Material"]) or
                                         k in normalize_str(row["modelo_limpio"]) or
                                         k in normalize_str(row["especificaciones"]) for k in mod_keywords), axis=1)
                results = results[mask]
        
        return results

    @staticmethod
    def format_inventory_context(results: pd.DataFrame) -> str:
        """Formats the filtered inventory results into a human-readable string for the AI prompt."""
        if results.empty:
            return "No se encontraron productos que coincidan exactamente con la búsqueda."

        try:
            available_specs = os.listdir(SPECS_DIR)
            with open(SPECS_MAPPING_FILE, "r", encoding="utf-8") as f:
                manual_map = json.load(f)
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                expert_data = json.load(f)
                expert_tips = {item['sku']: item.get('tip_venta') for item in expert_data if item.get('tip_venta')}
        except:
            available_specs, manual_map, expert_tips = [], {}, {}

        # Sort and limit
        results = results.sort_values(by=["CantDisponible"], ascending=False)
        results = results.drop_duplicates(subset=["Material"], keep="first")
        results = results.sort_values(by=["CantDisponible", "Precio Contado"], ascending=[False, False]).head(20)
        
        inventory_context = ""
        for _, item in results.iterrows():
            match = resolve_spec_match(item['Material'], item['Subproducto'], available_specs, manual_map)
            has_image = "NO"
            if match and isinstance(match, str):
                if any(match.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    has_image = "SI"
            
            ficha_tag = "SI" if match else "NO"
            try:
                raw_price = item.get('Precio Contado', 0)
                precio = f"${float(raw_price):,.0f}" if pd.notnull(raw_price) and str(raw_price).replace('.','',1).isdigit() else str(raw_price)
            except: precio = str(item.get('Precio Contado', '-'))

            sku_str = str(item['Material'])
            final_tip = expert_tips.get(sku_str, item.get('tip_venta', '-'))
            if not final_tip or final_tip == "nan" or pd.isna(final_tip): final_tip = "-"

            try: stock_val = int(float(item.get('CantDisponible', 0)))
            except: stock_val = 0

            line = f"- [ID: {item['Material']}] MODELO: {item['Subproducto']} | FICHA: {ficha_tag} | IMG: {has_image} | CATEGORIA: {item['categoria']} | MARCA: {item['marca']} | DESC: {item.get('especificaciones', '-')} | STOCK: {stock_val} | PRECIO CONTADO: {precio} | TIP: {final_tip}\n"
            inventory_context += line
            
        return inventory_context

inventory_service = InventoryService()
