from scrapers.base import fetch_json ,polite_delay, save_to_json
from scrapers.tag_cleaner import clean_entries
import os

BASE_URL = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/main/data/class/{}"

SOURCES = [
    "class-artificer.json",
    "class-barbarian.json",
    "class-bard.json",
    "class-cleric.json",
    "class-druid.json",
    "class-fighter.json",
    "class-monk.json",
    "class-paladin.json",
    "class-ranger.json",
    "class-rogue.json",
    "class-sorcerer.json",
    "class-warlock.json",
    "class-wizard.json"
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CLASSES    = os.path.join(ROOT, "data", "dnd", "classes.json")
OUTPUT_SUBCLASSES = os.path.join(ROOT, "data", "dnd", "subclasses.json")

def parse_hit_die(raw):
    if not raw:
        return 'Unknown'
    return f"{raw.get('number',1)}d{raw.get('faces',6)}"
def parsec_class(raw):
    name = raw.get('name', 'Unknown')
    dnd_class={
        'name': name,
        'universe':'dnd',
        'source':'5etools',
        'content_type':'class',
        'description': clean_entries(raw.get('entries',[])),
        'hit_die':parse_hit_die(raw.get('hd')),
        'proficiencies': raw.get('proficiency',[]),
        'srd': raw.get('srd', False)
    }
    return dnd_class
def parsec_subclass(raw):
    name = raw.get('name', 'Unknown')
    dnd_subclass={
        'name': name,
        'universe':'dnd',
        'source':'5etools',
        'content_type':'subclass',
        'description': clean_entries(raw.get('entries',[])),
        'class':raw.get('className',[]),
        'srd': raw.get('srd', False)
    }
    return dnd_subclass

def run():
    seen_classes = {}
    seen_subclasses={}

    for source_file in SOURCES:
        url = BASE_URL.format(source_file)
        print(f"\nFetching {source_file}...")

        data = fetch_json(url)
        if not data:
            print(f"  Failed, skipping.")
            continue

            # 1. Process Classes
        raw_classes = data.get("class", [])
        print(f"  {len(raw_classes)} classes found")
        for raw in raw_classes:
            parsed_cls = parsec_class(raw)
            seen_classes[parsed_cls["name"]] = parsed_cls

            # 2. Process Subclasses (Fixed key from "spell" to "subclass")
        raw_subclasses = data.get("subclass", [])
        print(f"  {len(raw_subclasses)} subclasses found")
        for raw in raw_subclasses:
                # Fixed: Call parse_subclass instead of parse_class
            parsed_sub = parsec_subclass(raw)
            seen_subclasses[parsed_sub["name"]] = parsed_sub

        polite_delay()

        # Save unique classes
        all_classes = list(seen_classes.values())
        print(f"\nTotal unique classes: {len(all_classes)}")
        save_to_json(all_classes, OUTPUT_CLASSES)
        print("Classes saved successfully!")

        # Save unique subclasses
        all_subclasses = list(seen_subclasses.values())
        print(f"Total unique subclasses: {len(all_subclasses)}")
        save_to_json(all_subclasses, OUTPUT_SUBCLASSES)
        print("Subclasses saved successfully!")

if __name__ == "__main__":
    run()

