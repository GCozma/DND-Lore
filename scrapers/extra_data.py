# scrapers/test_query.py
import sqlite3
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lore_oracle.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find Fireball
cursor.execute("SELECT * FROM content WHERE name = ?", ("Fireball",))
row = cursor.fetchone()

print("Raw row:", row)
print()

# Unpack it — column order matches the table definition
id, name, universe, source, content_type, description, extra_data = row

print("Name:", name)
print("Type:", content_type)
print("Description:", description[:100], "...")
print()

# Parse the JSON blob back into a real dict
extra = json.loads(extra_data)
print("Extra data:", json.dumps(extra, indent=2))

conn.close()