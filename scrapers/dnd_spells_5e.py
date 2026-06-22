# scrapers/dnd_spells_5e.py
import os
from scrapers.base import fetch_json, polite_delay, save_to_json
from scrapers.tag_cleaner import clean_entries

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "dnd", "spells.json")

BASE_URL = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/spells/{}"

# All 17 spell source files — ordered oldest to newest
# Same deduplication logic as monsters: later source overwrites earlier
SOURCES = [
    "spells-phb.json",       # Player's Handbook
    "spells-ggr.json",       # Guildmasters' Guide to Ravnica
    "spells-ai.json",        # Acquisitions Incorporated
    "spells-egw.json",       # Explorer's Guide to Wildemount
    "spells-idrotf.json",    # Icewind Dale: Rime of the Frostmaiden
    "spells-ftd.json",       # Fizban's Treasury of Dragons
    "spells-tce.json",       # Tasha's Cauldron of Everything
    "spells-scc.json",       # Strixhaven: A Curriculum of Chaos
    "spells-aag.json",       # Astral Adventurer's Guide
    "spells-sato.json",      # Spelljammer: Adventures in Space
    "spells-bmt.json",       # Book of Many Things
    "spells-llk.json",       # Lost Laboratory of Kwalish
    "spells-aitfr-avt.json", # Adventures in the Forgotten Realms
    "spells-frhof.json",     # Fables of the Forgotten Realms
    "spells-efa.json",       # Even Farther Realms
]

# ── LOOKUP TABLES ─────────────────────────────────────────────────────────────
SCHOOL_MAP = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
    "V": "Evocation"
}
# ── FIELD MAPPING FUNCTIONS ───────────────────────────────────────────────────
def parse_school(raw):
    """
    "E" → "Evocation"
    Single letter code, looked up in SCHOOL_MAP.
    """
    return SCHOOL_MAP.get(raw, raw)


def parse_time(raw):
    """
    [{"number": 1, "unit": "action"}]   → "1 action"
    [{"number": 1, "unit": "reaction"}] → "1 reaction"
    [{"number": 10, "unit": "minute"}]  → "10 minutes"
    """
    if not raw:
        return "Unknown"
    first = raw[0]
    number = first.get("number", 1)
    unit   = first.get("unit", "")

    # Pluralise the unit if number > 1
    if number > 1:
        unit += "s"

    return f"{number} {unit}"


def parse_range(raw):
    """
    {"type": "point", "distance": {"type": "feet", "amount": 150}} → "150 feet"
    {"type": "special"}  → "Special"
    {"type": "cone"}     → "Cone"
    """
    if not raw:
        return "Unknown"

    range_type = raw.get("type", "")

    # These types have no distance — they ARE the range description
    if range_type in ("special", "cone", "line", "radius",
                      "hemisphere", "sphere", "cube"):
        return range_type.capitalize()

    # Point range — has a nested distance object
    distance = raw.get("distance", {})
    amount   = distance.get("amount")
    unit     = distance.get("type", "")

    if amount is not None:
        return f"{amount} {unit}"

    # Self, touch, sight, unlimited
    return unit.capitalize() if unit else "Unknown"


def parse_components(raw):
    """
    {"v": true, "s": true, "m": "a tiny ball of bat guano"}
    → {"verbal": True, "somatic": True, "material": "a tiny ball of bat guano"}

    Renames the single-letter keys to readable names.
    """
    if not raw:
        return {}
    return {
        "verbal":   raw.get("v", False),
        "somatic":  raw.get("s", False),
        "material": raw.get("m", False)  # False if no material, string if yes
    }


def parse_duration(raw):
    """
    [{"type": "instant"}]                              → "Instantaneous"
    [{"type": "timed", "duration": {"type": "minute", "amount": 1}}] → "1 minute"
    [{"type": "permanent"}]                            → "Permanent"
    """
    if not raw:
        return "Unknown"

    first = raw[0]
    dtype = first.get("type", "")

    if dtype == "instant":
        return "Instantaneous"
    if dtype == "permanent":
        return "Permanent"
    if dtype == "special":
        return "Special"

    # Timed duration — has a nested duration object
    if dtype == "timed":
        dur    = first.get("duration", {})
        amount = dur.get("amount", 1)
        unit   = dur.get("type", "")
        if amount > 1:
            unit += "s"

        # Concentration spells have an extra flag
        conc = first.get("concentration", False)
        text = f"{amount} {unit}"
        if conc:
            text = f"Concentration, up to {text}"
        return text

    return dtype.capitalize()


def parse_spell(raw):
    """
    Takes one raw 5etools spell dict and returns one clean entry
    in our consistent schema.
    """
    # Description: main entries + higher level entries combined
    description_parts = []

    main_text = clean_entries(raw.get("entries", []))
    if main_text:
        description_parts.append(main_text)

    higher = clean_entries(raw.get("entriesHigherLevel", []))
    if higher:
        description_parts.append(higher)

    description = "\n\n".join(description_parts)

    return {
        # ── Shared base fields ──
        "name":         raw.get("name", "Unknown"),
        "universe":     "dnd",
        "source":       "5etools",
        "content_type": "spell",
        "description":  description,

        # ── Spell-specific fields ──
        "level":        raw.get("level", 0),
        "school":       parse_school(raw.get("school", "")),
        "casting_time": parse_time(raw.get("time", [])),
        "range":        parse_range(raw.get("range", {})),
        "components":   parse_components(raw.get("components", {})),
        "duration":     parse_duration(raw.get("duration", [])),
        "damage_types": raw.get("damageInflict", []),
        "saving_throw": raw.get("savingThrow", []),
        "srd":          raw.get("srd", False)
    }


# ── RUN ───────────────────────────────────────────────────────────────────────
def run():
    seen = {}   # name → spell, for deduplication

    for source_file in SOURCES:
        url = BASE_URL.format(source_file)
        print(f"\nFetching {source_file}...")

        data = fetch_json(url)
        if not data:
            print(f"  Failed, skipping.")
            continue

        spells = data.get("spell", [])
        print(f"  {len(spells)} spells found")

        for raw in spells:
            spell = parse_spell(raw)
            seen[spell["name"]] = spell  # later source overwrites earlier

        polite_delay()

    all_spells = list(seen.values())
    print(f"\nTotal unique spells: {len(all_spells)}")
    save_to_json(all_spells, OUTPUT)
    print("Done!")


# ── TEST ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run()