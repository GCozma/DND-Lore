from scrapers.base import fetch_json ,polite_delay, save_to_json
from scrapers.tag_cleaner import clean_entries
import os

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "dnd", "deities.json")

DEITIES_URL = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/deities.json"

ALIGNMENT_MAP = {
    "L": "Lawful", "N": "Neutral", "C": "Chaotic",
    "G": "Good",   "E": "Evil",    "U": "Unaligned", "A": "Any"
}

def parse_alignment(raw):
    if not raw:
        return "Unknown"
    parts = []
    for code in raw:
        if isinstance(code, str):
            # Normal case — a letter code like "L", "E", "N"
            parts.append(ALIGNMENT_MAP.get(code, code))
        elif isinstance(code, dict):
            # Special case — something like {"special": "any non-good alignment"}
            special = code.get("special", "")
            if special:
                parts.append(special)  # use the special description directly

    return " ".join(parts) if parts else "Unknown"

def parse_deities(raw):
    name=raw.get('name','Unknown')
    deities={
        'name': name,
        'universe':'dnd',
        'alignment': parse_alignment(raw.get('alignment')),
        'source':'5etools',
        'content_type':'deity',
        'description':clean_entries(raw.get('entries',[])),
        'pantheon':raw.get('pantheon',""),
        'domains':raw.get('domains',[]),
        'title':raw.get('title',''),
        'srd':raw.get('srd',False),
        'worshipers': raw.get('worshipers', ''),
        'symbol': raw.get('symbol', ''),
    }
    return deities

def run():
    seen={}
    print('Fetching deities...')
    data=fetch_json(DEITIES_URL)
    if not data:
        print(f"  Failed, skipping.")
        return

    deities = data.get("deity", [])
    print(f"  {len(deities)} items found")

    for raw in deities:
        deity = parse_deities(raw)
        name = deity["name"]

        if name not in seen:
            seen[name] = deity
        else:
            # Already seen this deity — only overwrite if the new one
            # has a description and the existing one doesn't
            existing_has_desc = bool(seen[name]["description"])
            new_has_desc = bool(deity["description"])

            if new_has_desc and not existing_has_desc:
                seen[name] = deity
            elif new_has_desc and existing_has_desc:
                seen[name] = deity  # both have desc, keep the later/newer one
            # else: keep existing (it has description, new one doesn't)

    polite_delay()

    all_deities = list(seen.values())
    print(f"\nTotal unique deities: {len(all_deities)}")
    save_to_json(all_deities, OUTPUT)
    print("Done!")

if __name__=='__main__':
    run()
