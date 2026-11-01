# Builds data/collection.json from the card list in data/catalogue.json,
# with live prices from TCGdex (Pokémon) and Limitless (One Piece).
# Usage: python scripts/build_collection.py [data/catalogue.json] [data/collection.json]
import sys, json, re, time, urllib.request

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/catalogue.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/collection.json"
FIELDS = ["Record ID", "Brand", "Language", "Set code", "Card name", "Card number", "Printed rarity",
          "Finish / variant", "Quantity (minimum)", "Quantity basis", "Condition", "Low estimate EUR",
          "High estimate EUR", "Value status", "Estimate date", "ID status", "Period", "Chat reference",
          "Photo reference", "Notes"]
RATE = 52.95
UA = {"User-Agent": "Mozilla/5.0 (collector dashboard)"}

def get(url, as_json=True):
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode()
            return json.loads(r) if as_json else r
        except Exception as e:
            err = e; time.sleep(1)
    return None

SETS = {
    "CRI": ("fr", "me04", "Chaos Ascendant (ME04)"),
    "PBL": ("fr", "me05", "Nuit Noire (ME05)"),
    "PFL": ("fr", "me02", "Flammes Fantasmagoriques (ME02)"),
    "SV1": ("fr", "sv01", "Écarlate et Violet (SV1)"),
    "SVE": ("fr", "sve", "Énergies de base"),
    "M1S": ("ja", "M1S", "Mega Symphonia (M1S)"),
    "SV2a": ("ja", "SV2a", "Pokémon Card 151 (SV2a)"),
    "SV8": ("ja", "SV8", "Super Electric Breaker (SV8)"),
    "OP-17": (None, None, "OP-17 The World's Strongest Warriors"),
    "OP-15": (None, None, "OP-15 Adventure on Kami's Island"),
}
LANG = {"French": "FR", "Japanese": "JP", "English": "EN"}

def eur(x): return f"€{x:,.2f}"
def mur(x): return f"Rs {round(x*RATE):,}"

with open(SRC, encoding="utf-8") as f:
    catalogue = json.load(f)
rows = []
for c in catalogue:
    rid, brand, lang, setc, name, num, rar, fin, qty, qb, cond, lo, hi, vs, ed, ids, per, chat, photo, notes = (c.get(k) for k in FIELDS)
    if not rid: continue
    game = "Pokémon" if brand.startswith("Pok") else "One Piece"
    lang_code, set_id, set_name = SETS.get(setc, (None, None, "Set not identified"))
    fin_l = (fin or "").lower()
    price = None; demand = ""; basis = ""
    if game == "Pokémon" and set_id and num:
        local = num.split("/")[0]
        d = get(f"https://api.tcgdex.net/v2/{lang_code}/cards/{set_id}-{local}")
        cm = (d or {}).get("pricing", {}) or {}
        cm = cm.get("cardmarket") or {}
        if cm:
            want_holo = "reverse" in fin_l
            t = cm.get("trend-holo") if want_holo else cm.get("trend")
            a7 = cm.get("avg7-holo") if want_holo else cm.get("avg7")
            a30 = cm.get("avg30-holo") if want_holo else cm.get("avg30")
            if not t:  # no separate reverse price: fall back to the card's own price
                t, a7, a30 = cm.get("trend"), cm.get("avg7"), cm.get("avg30")
            if t:
                price = float(t); basis = "Cardmarket trend"
                if a7 and a30:
                    ch = (a7 - a30) / a30
                    demand = "Rising" if ch > 0.10 else "Falling" if ch < -0.10 else "Steady"
    elif game == "One Piece" and num:
        h = get(f"https://onepiece.limitlesstcg.com/cards/{num}", as_json=False)
        m = re.search(r'card-price eur">€([0-9.,]+)<', h or "")
        if m:
            price = float(m.group(1).replace(",", "")); basis = "English market price (Limitless / Cardmarket)"
    est = False
    if price is None and (lo is not None or hi is not None):
        price = float(hi if hi is not None else lo); est = True
    q = int(qty) if qty else None
    if price is not None and price < 0.5 and not est:
        demand = "Bulk"
    if price is not None:
        ptxt = (f"€{lo:g}–{hi:g} (estimate)" if est and lo is not None and hi is not None else f"{eur(price)} (≈ {mur(price)})")
    else:
        ptxt = "Not priced yet"
    bits = []
    if game == "One Piece" and price is not None and not est and lang in ("French", "Japanese"):
        bits.append(f"Price is for the English card as a guide; {LANG.get(lang, lang)} copies can differ.")
    if "cosmos" in fin_l:
        bits.append("Cosmos holo promo version; price shown is the regular card.")
    if "poké ball" in fin_l:
        bits.append("Poké Ball reverse holo.")
    if ids == "Chat only": bits.append("Not photo-checked yet.")
    elif ids == "Needs details": bits.append("Needs card number to price.")
    elif ids == "Ownership uncertain": bits.append("Not sure you own this one.")
    if est: bits.append("Older estimate from your notes, not a live price.")
    if rar and "SR" in str(rar) and "print unclear" in str(rar): bits.append("Check whether it's a parallel (alternate art): worth far more if so.")
    card = name + (f" {num}" if num else "")
    rarity = str(rar or "").replace(" (reported)", "").replace(" (provisional)", "")
    value = round((price or 0) * (q or 1), 2) if not est else round(((lo or 0) + (hi or 0)) / 2 * (q or 1), 2)
    rows.append({
        "id": rid, "card": card, "game": game, "set": set_name, "language": LANG.get(lang, lang),
        "rarity": rarity, "finish": fin or "", "condition": "Not graded",
        "qty": q if q else "?", "price": ptxt, "price_eur": round(price, 2) if price is not None and not est else None,
        "value_eur": value, "demand": demand, "note": " ".join(bits),
    })
    time.sleep(0.15)

rows.sort(key=lambda x: -(x["value_eur"] or 0))
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
priced = [r for r in rows if r["price_eur"] is not None]
print("rows", len(rows), "live-priced", len(priced), "total value", round(sum(r["value_eur"] for r in rows), 2))
for r in rows[:20]: print(r["card"], "|", r["price"], "|", r["demand"])
