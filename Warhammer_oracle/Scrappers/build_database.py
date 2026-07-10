# warhammer_oracle/Scrappers/build_database.py
import sqlite3
import json
import os

from Scrappers.constants import ROOT, DB_PATH, DATA_DIR

# JSON files paired with their content type
SOURCE_FILES = [
    ("factions.json", "faction"),
    ("units.json", "unit"),
    ("lore.json", "lore")
]

# Fields that get dedicated database columns. Leftovers get bundled into extra_data.
KNOWN_FIELDS = {"name", "universe", "source", "content_type", "description"}


def create_table(cursor):
    """Creates the SQLite content table if it doesn't already exist."""
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_name ON content(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON content(content_type)")


def load_json_file(filepath):
    """Reads a JSON file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def split_entry(entry):
    """Splits an entry, unpacking nested extra_data fields to ensure flat SQL querying."""
    # Flatten nested extra_data dictionary if present
    entry_flat = entry.copy()
    if "extra_data" in entry_flat and isinstance(entry_flat["extra_data"], dict):
        for k, v in entry_flat["extra_data"].items():
            entry_flat[k] = v
        del entry_flat["extra_data"]

    name = entry_flat.get("name", "Unknown")
    universe = entry_flat.get("universe", "wh40k")
    source = entry_flat.get("source", "")
    content_type = entry_flat.get("content_type", "")
    description = entry_flat.get("description", "")

    # Bundle all other custom fields into a leftover dictionary
    extra = {
        key: value
        for key, value in entry_flat.items()
        if key not in KNOWN_FIELDS
    }
    extra_json = json.dumps(extra, ensure_ascii=False)

    return (name, universe, source, content_type, description, extra_json)


def insert_entries(cursor, entries, content_type):
    """Inserts a list of entries into the table."""
    rows = [split_entry(entry) for entry in entries]

    cursor.executemany("""
        INSERT INTO content (name, universe, source, content_type, description, extra_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    print(f"  Inserted {len(rows)} {content_type} entries")


def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    create_table(cursor)

    # Clear old entries in case of re-runs
    cursor.execute("DELETE FROM content")

    for relative_path, content_type in SOURCE_FILES:
        filepath = os.path.join(DATA_DIR, relative_path)
        if not os.path.exists(filepath):
            print(f"Skipping {relative_path} (File not found)")
            continue

        print(f"Loading {relative_path}...")
        entries = load_json_file(filepath)
        insert_entries(cursor, entries, content_type)

    conn.commit()

    # Query row count
    cursor.execute("SELECT COUNT(*) FROM content")
    total = cursor.fetchone()[0]
    print(f"\nTotal rows in SQLite database: {total}")

    conn.close()
    print(f"Database saved to {DB_PATH}")


if __name__ == "__main__":
    run()