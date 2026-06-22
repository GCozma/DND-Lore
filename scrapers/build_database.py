# scrapers/build_database.py
import sqlite3
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lore_oracle.db")

# Every JSON file we've built, paired with its content type
SOURCE_FILES = [
    ("dnd/spells.json",      "spell"),
    ("dnd/monsters.json",    "monster"),
    ("dnd/items.json",       "item"),
    ("dnd/classes.json",     "class"),
    ("dnd/subclasses.json",  "subclass"),
    ("dnd/deities.json",     "deity"),
    ("dnd/regions.json",     "region"),
]

# These 5 fields get their own real columns.
# Everything else on each entry gets bundled into extra_data.
KNOWN_FIELDS = {"name", "universe", "source", "content_type", "description"}


def create_table(cursor):
    """
    Creates the content table if it doesn't already exist.
    IF NOT EXISTS means: don't crash if we run this again later,
    just skip creating it if it's already there.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            universe      TEXT NOT NULL,
            source        TEXT,
            content_type  TEXT NOT NULL,
            description   TEXT,
            extra_data    TEXT
        )
    """)


def load_json_file(filepath):
    """Same pattern as load_json in base.py — reads a JSON file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def split_entry(entry):
    """
    Takes one entry dict (e.g. one spell) and splits it into:
      - the 5 known fields, as separate values
      - everything else, bundled into one JSON string

    This is the core transformation: 15+ different schemas
    (spell fields, monster fields, item fields...) all collapse
    into the same 6-column shape.
    """
    name         = entry.get("name", "Unknown")
    universe     = entry.get("universe", "")
    source       = entry.get("source", "")
    content_type = entry.get("content_type", "")
    description  = entry.get("description", "")

    # Build a new dict containing only the fields NOT in KNOWN_FIELDS
    # This is a dictionary comprehension, same pattern as parse_speed()
    # back in the monster scraper.
    extra = {
        key: value
        for key, value in entry.items()
        if key not in KNOWN_FIELDS
    }

    # Convert that leftover dict into a JSON string for storage.
    # SQLite has no "nested object" column type — it only stores
    # text, numbers, and a few other simple types. So we serialize
    # the dict into a JSON string here, and will parse it back into
    # a dict whenever we read a row back out later.
    extra_json = json.dumps(extra, ensure_ascii=False)

    return (name, universe, source, content_type, description, extra_json)


def insert_entries(cursor, entries, content_type):
    """
    Inserts a list of entries into the table.
    Uses cursor.executemany() — runs the same INSERT statement
    once per row, much faster than calling execute() in a loop.
    """
    rows = [split_entry(entry) for entry in entries]

    cursor.executemany("""
        INSERT INTO content (name, universe, source, content_type, description, extra_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    print(f"  Inserted {len(rows)} {content_type} entries")


def run():
    # Connect to (or create) the database file
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    create_table(cursor)

    # Clear the table first, in case we're re-running this script
    # after re-scraping data — avoids duplicate rows piling up
    cursor.execute("DELETE FROM content")

    data_dir = os.path.join(ROOT, "data")

    for relative_path, content_type in SOURCE_FILES:
        filepath = os.path.join(data_dir, relative_path)
        print(f"Loading {relative_path}...")

        entries = load_json_file(filepath)
        insert_entries(cursor, entries, content_type)

    # Nothing is actually saved to disk until you commit
    conn.commit()

    # Quick sanity check — count total rows
    cursor.execute("SELECT COUNT(*) FROM content")
    total = cursor.fetchone()[0]
    print(f"\nTotal rows in database: {total}")

    conn.close()
    print(f"Database saved to {DB_PATH}")


if __name__ == "__main__":
    run()