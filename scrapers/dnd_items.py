from scrapers.base import fetch_json ,polite_delay, save_to_json
from scrapers.tag_cleaner import clean_entries
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "dnd", "items.json")

ITEMS_URL="https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/items.json"

TYPE_MAP = {
    "A":   "Ammunition",
    "AIR": "Vehicle (Air)",
    "EXP": "Explosive",
    "FD":  "Food & Drink",
    "G":   "Adventuring Gear",
    "GS":  "Gaming Set",
    "HA":  "Heavy Armor",
    "INS": "Instrument",
    "LA":  "Light Armor",
    "M":   "Melee Weapon",
    "MA":  "Medium Armor",
    "MNT": "Mount",
    "OTH": "Other",
    "P":   "Potion",
    "R":   "Ranged Weapon",
    "RD":  "Rod",
    "RG":  "Ring",
    "S":   "Shield",
    "SC":  "Scroll",
    "SCF": "Spellcasting Focus",
    "SHP": "Vehicle (Water)",
    "SPC": "Vehicle (Space)",
    "T":   "Tool",
    "TAH": "Tack & Harness",
    "TB":  "Treasure",
    "TG":  "Trade Good",
    "VEH": "Vehicle (Land)",
    "WD":  "Wand",
    "$A":  "Currency",
    "$C":  "Currency",
    "$G":  "Currency",
}

def parse_type(raw):
    if not raw:
        return "Unknown"
    base=raw.split('|')[0]
    return TYPE_MAP.get(base,base)

def parse_attunement(raw):
    if raw is None:
        return 'No'
    if isinstance(raw,bool):
        return 'Yes'
    if isinstance(raw,str):
        return f"Yes({raw})"
    return 'No'

def parse_rarity(raw):
    if not raw:
        return "Unknown"
    return raw

def parse_item(raw):
    name=raw.get('name','Unknown')
    items={
        "name": name,
        "universe": "dnd",
        "source": "5etools",
        "content_type":"item",
        'description': clean_entries(raw.get("entries", [])),
        'item_type':parse_type(raw.get('type')),
        'rarity': parse_rarity(raw.get('rarity')),
        'attunement':parse_attunement(raw.get('reqAttune')),
        'wondrous': raw.get('wondrous',False),
        'srd':raw.get('srd',False)
    }
    return items

def run():
    seen={}
    print('Fetching items...')
    data=fetch_json(ITEMS_URL)
    if not data:
        print(f"  Failed, skipping.")
        return

    items = data.get("item", [])
    print(f"  {len(items)} items found")

    for raw in items:
        item = parse_item(raw)
        seen[item["name"]] = item  # later source overwrites earlier

    polite_delay()

    all_items = list(seen.values())
    print(f"\nTotal unique items: {len(all_items)}")
    save_to_json(all_items, OUTPUT)
    print("Done!")

if __name__ == "__main__":
    run()

