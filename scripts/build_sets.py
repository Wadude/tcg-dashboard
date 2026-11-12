# Builds data/sets.json: every card of the sets the collector is completing,
# with Cardmarket prices (TCGdex for Pokémon, Limitless for One Piece).
# Usage: python scripts/build_sets.py [data/sets.json]
import sys, json, re, html, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1] if len(sys.argv) > 1 else "data/sets.json"
UA = {"User-Agent": "Mozilla/5.0 (collector dashboard)"}

def get(url, as_json=True):
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode()
            return json.loads(r) if as_json else r
        except Exception:
            time.sleep(1)
    return None

def tidy(name):
    """Limitless writes "Monkey.D.Luffy" and "Edward.Newgate"; show "Monkey D. Luffy" and "Edward Newgate"."""
    return re.sub(r"\b([A-Z]) ", r"\1. ", re.sub(r"\.(?=[A-Z])", " ", name))

rows = []

# Pokémon 30th Celebration, French names (the collector's language).
RARITY_30TH = {
    "Commune": ("Common", "Main set", 1), "Rare": ("Rare", "Main set", 1),
    "Double rare": ("Double rare", "Main set", 1), "Pikachu Rare": ("Classic Collection", "Main set", 1),
    "Illustration rare": ("Illustration rare", "Illustration rares", 2),
    "Illustration spéciale rare": ("Special illustration rare", "Special illustration rares", 3),
    "Futuristic Rare": ("Futuristic rare", "Special illustration rares", 3),
    "RGB Rare": ("RGB rare", "RGB Mews", 4),
}
s = get("https://api.tcgdex.net/v2/fr/sets/30th") or {"cards": []}
def card30(c):
    d = get(f"https://api.tcgdex.net/v2/fr/cards/{c['id']}") or {}
    cm = ((d.get("pricing") or {}).get("cardmarket")) or {}
    rarity, group, order = RARITY_30TH.get(d.get("rarity"), (d.get("rarity") or "", "Main set", 1))
    return {"id": c["id"], "set": "30th Celebration", "game": "Pokémon", "group": group, "group_order": order,
            "num": c.get("localId") or "", "name": d.get("name") or c.get("name") or "", "rarity": rarity,
            "price_eur": cm.get("trend")}
with ThreadPoolExecutor(8) as ex:
    rows += list(ex.map(card30, s["cards"]))

# One Piece OP-17, every print including alternate arts (English names).
page = get("https://onepiece.limitlesstcg.com/cards?q=set:OP17&display=list&show=all", as_json=False) or ""
seen = {}
for m in re.finditer(r'<tr data-hover="([^"]+)">(.*?)</tr>', page, re.S):
    img, b = m.groups()
    tds = [html.unescape(re.sub(r"<[^>]+>", "", t)).strip() for t in re.findall(r"<td[^>]*>(.*?)</td>", b, re.S)]
    if len(tds) < 2:
        continue
    code, name = tds[0], tds[1]
    rarity = tds[3] if len(tds) > 3 else ""
    e = re.search(r'card-price eur"[^>]*>([\d.,]+)€', b)
    p = re.search(r"_(p\d+)_EN", img)
    if not code.startswith("OP17"):
        group, order, label = "Special cards", 4, "Special card"
    elif not p:
        group, order, label = "Main set", 1, rarity
    elif p.group(1) == "p1":
        group, order, label = "Alt arts", 2, "Alt art"
    else:
        group, order, label = "Super parallels", 3, "Super parallel"
    cid = code + ("-" + p.group(1) if p else "")
    if cid in seen:
        continue
    seen[cid] = True
    rows.append({"id": cid, "set": "OP-17", "game": "One Piece", "group": group, "group_order": order,
                 "num": code, "name": tidy(name), "rarity": label,
                 "price_eur": float(e.group(1).replace(",", "")) if e else None})

rows.sort(key=lambda r: (r["set"], r["group_order"], r["num"], r["id"]))
for i, r in enumerate(rows):
    r["order"] = i
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
for st in ("30th Celebration", "OP-17"):
    part = [r for r in rows if r["set"] == st]
    print(st, len(part), "cards,", sum(1 for r in part if r["price_eur"] is not None), "priced")
