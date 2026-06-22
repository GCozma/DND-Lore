# scrapers/dnd_monsters.py
import json
from scrapers.base import fetch_json, polite_delay, save_to_json
from scrapers.tag_cleaner import clean_tag, clean_entries
import os


# __file__ is the path of the current file (dnd_monsters.py)
# os.path.dirname() gets its folder (scrapers/)
# os.path.dirname() again goes up one level (project root)
# os.path.join() then builds the full path from there
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "dnd", "monsters.json")

# ── URLS ──────────────────────────────────────────────────────────────────────
# 5etools splits data across multiple files, one per sourcebook.
# We start with the Monster Manual — we'll add more sources later.
SOURCES = [
    {
        "stats": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/bestiary-mm.json",
        "fluff": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/fluff-bestiary-mm.json",
        "label": "MM"
    },
    {
        "stats": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/bestiary-vgm.json",
        "fluff": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/fluff-bestiary-vgm.json",
        "label": "VGM"  # Volo's Guide to Monsters
    },
    {
        "stats": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/bestiary-mtf.json",
        "fluff": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/fluff-bestiary-mtf.json",
        "label": "MTF"  # Mordenkainen's Tome of Foes
    },
    {
        "stats": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/bestiary-ftd.json",
        "fluff": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/fluff-bestiary-ftd.json",
        "label": "FTD"  # Fizban's Treasury of Dragons
    },
    {
        "stats": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/bestiary-mpmm.json",
        "fluff": "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/bestiary/fluff-bestiary-mpmm.json",
        "label": "MPMM" # Mordenkainen Presents: Monsters of the Multiverse
    }
]

# ── LOOKUP TABLES ─────────────────────────────────────────────────────────────
SIZE_MAP = {
    "T": "Tiny", "S": "Small", "M": "Medium",
    "L": "Large", "H": "Huge", "G": "Gargantuan"
}

ALIGNMENT_MAP = {
    "L": "Lawful", "N": "Neutral", "C": "Chaotic",
    "G": "Good",   "E": "Evil",    "U": "Unaligned", "A": "Any"
}

# ── FIELD MAPPING FUNCTIONS ───────────────────────────────────────────────────
def parse_size(raw):
    if not raw:
        return "Unknown"
    return SIZE_MAP.get(raw[0], raw[0])

def parse_type(raw):
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("type", "Unknown")
    return "Unknown"

def parse_ac(raw):
    if not raw:
        return None
    first = raw[0]
    if isinstance(first, int):
        return first
    if isinstance(first, dict):
        return first.get("ac")
    return None

def parse_hp(raw):
    if not raw:
        return {"average": None, "formula": None}
    return {
        "average": raw.get("average"),
        "formula": raw.get("formula")
    }

def parse_speed(raw):
    if not raw:
        return {}
    return {
        k: v for k, v in raw.items()
        if k != "canHover" and isinstance(v, (int, float))
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
    words = [ALIGNMENT_MAP.get(code, code) for code in raw]
    return " ".join(words)

def parse_abilities(monster):
    return {
        "str": monster.get("str"),
        "dex": monster.get("dex"),
        "con": monster.get("con"),
        "int": monster.get("int"),
        "wis": monster.get("wis"),
        "cha": monster.get("cha")
    }

def parse_traits(raw_list):
    """
    Converts a list of trait/action dicts into clean text entries.
    Each item has a "name" and "entries" field.
    Returns a list of {"name": ..., "text": ...} dicts.
    """
    if not raw_list:
        return []
    result = []
    for item in raw_list:
        name = item.get("name", "")
        text = clean_entries(item.get("entries", []))
        result.append({"name": name, "text": text})
    return result

# ── LORE BUILDER ──────────────────────────────────────────────────────────────
def build_fluff_index(fluff_data):
    """
    The fluff file is a list — we need to look up monsters by name quickly.
    Instead of looping through 444 entries every time, we build a dict:
        {"Aboleth": {...}, "Dragon": {...}, ...}
    Then lookup is instant: fluff_index["Aboleth"]

    This is called building an INDEX — trading memory for speed.
    """
    index = {}
    for entry in fluff_data.get("monsterFluff", []):
        index[entry["name"]] = entry
    return index

def parse_lore(fluff_entry):
    """
    Extracts and cleans lore text from a fluff entry.
    Uses clean_entries() — same function as traits/actions,
    because it's the same nested entries format.
    """
    if not fluff_entry:
        return ""
    raw_entries = fluff_entry.get("entries", [])
    return clean_entries(raw_entries)

# ── MAIN PARSER ───────────────────────────────────────────────────────────────
def parse_monster(raw, fluff_index):
    """
    Takes one raw 5etools monster dict and returns one clean entry
    in our consistent schema. Merges in lore from the fluff index.
    """
    name = raw.get("name", "Unknown")

    monster = {
        # ── Shared base fields (same on every content type) ──
        "name":         name,
        "universe":     "dnd",
        "source":       "5etools",
        "content_type": "monster",
        "description":  parse_lore(fluff_index.get(name)),

        # ── Monster-specific fields ──
        "cr":           raw.get("cr", "Unknown"),
        "size":         parse_size(raw.get("size")),
        "type":         parse_type(raw.get("type")),
        "alignment":    parse_alignment(raw.get("alignment")),
        "ac":           parse_ac(raw.get("ac")),
        "hp":           parse_hp(raw.get("hp")),
        "speed":        parse_speed(raw.get("speed")),
        "abilities":    parse_abilities(raw),
        "senses":       raw.get("senses", []),
        "languages":    raw.get("languages", []),
        "traits":       parse_traits(raw.get("trait")),
        "actions":      parse_traits(raw.get("action")),
        "environment":  raw.get("environment", []),
        "srd":          raw.get("srd", False)
    }

    return monster

# ── RUN ───────────────────────────────────────────────────────────────────────
def run():
    all_monsters = []
    seen = {}  # name → monster, for deduplication

    for source in SOURCES:
        print(f"\n=== Fetching {source['label']} ===")

        stats_data = fetch_json(source["stats"])
        fluff_data = fetch_json(source["fluff"])

        if not stats_data:
            print(f"Failed to fetch stats for {source['label']}, skipping.")
            continue

        fluff_index = build_fluff_index(fluff_data) if fluff_data else {}
        monsters = stats_data["monster"]
        print(f"Processing {len(monsters)} monsters...")

        for i, raw in enumerate(monsters):
            monster = parse_monster(raw, fluff_index)
            name = monster["name"]

            if name not in seen:
                seen[name] = monster  # first time seeing it — keep it
            else:
                # Already have this monster — overwrite with newer sourcebook
                # SOURCES is ordered oldest → newest, so later = more recent
                seen[name] = monster
                print(f"  ~ Updated duplicate: {name} ({source['label']})")

            if (i + 1) % 50 == 0:
                print(f"  ✓ {i + 1}/{len(monsters)}")

        polite_delay()

    # Convert the dict back to a list
    all_monsters = list(seen.values())

    print(f"\nTotal unique monsters: {len(all_monsters)}")
    save_to_json(all_monsters, OUTPUT)
    print(f"Done! {len(all_monsters)} monsters saved.")

# ── TEST ──────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     # Test on Aboleth only first
#     print("=== TEST: Single monster ===\n")
#
#     stats_data = fetch_json(SOURCES[0]["stats"])
#     fluff_data = fetch_json(SOURCES[0]["fluff"])
#     fluff_index = build_fluff_index(fluff_data)
#
#     monsters = stats_data["monster"]
#     aboleth_raw = next(m for m in monsters if m["name"] == "Aboleth")
#     aboleth = parse_monster(aboleth_raw, fluff_index)
#
#     print(json.dumps(aboleth, indent=2))
if __name__ == "__main__":
    run()