# warhammer_oracle/Scrappers/wh40k_units.py
import urllib.request
import csv
import io
import re
from Scrappers.base import save_to_json
from Scrappers.constants import DATA_DIR, os

CSV_URLS = {
    "factions": "https://wahapedia.ru/wh40k10ed/Factions.csv",
    "datasheets": "https://wahapedia.ru/wh40k10ed/Datasheets.csv",
    "models": "https://wahapedia.ru/wh40k10ed/Datasheets_models.csv",
    "wargear": "https://wahapedia.ru/wh40k10ed/Datasheets_wargear.csv"
}


def fetch_csv_data(url):
    """Downloads a CSV file and decodes it safely, handling Byte-Order Marks (BOM)."""
    print(f"Downloading CSV from: {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            # Decode using 'utf-8-sig' to automatically strip BOM (\ufeff)
            return response.read().decode("utf-8-sig")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return None


def run():
    # 1. Fetch all raw CSV tables
    factions_csv = fetch_csv_data(CSV_URLS["factions"])
    datasheets_csv = fetch_csv_data(CSV_URLS["datasheets"])
    models_csv = fetch_csv_data(CSV_URLS["models"])
    wargear_csv = fetch_csv_data(CSV_URLS["wargear"])

    if not all([factions_csv, datasheets_csv, models_csv, wargear_csv]):
        print("❌ Pipeline failed: Could not retrieve all CSV files.")
        return

    # 2. Parse Faction Map (ID -> Name)
    print("Parsing factions...")
    faction_map = {}
    f_reader = csv.DictReader(io.StringIO(factions_csv), delimiter='|')
    for row in f_reader:
        faction_map[row['id']] = row['name']

    # 3. Parse Models (Datasheet ID -> List of Models/Stats)
    print("Parsing unit model profiles...")
    models_map = {}
    m_reader = csv.DictReader(io.StringIO(models_csv), delimiter='|')
    for row in m_reader:
        ds_id = row['datasheet_id']
        if ds_id not in models_map:
            models_map[ds_id] = []
        models_map[ds_id].append({
            "name": row['name'],
            "m": row['M'],
            "t": row['T'],
            "sv": row['Sv'],
            "invulnerable": row['inv_sv'] if row['inv_sv'] else "None",
            "w": row['W'],
            "ld": row['Ld'],
            "oc": row['OC']
        })

    # 4. Parse Weapons/Wargear (Datasheet ID -> List of Weapons)
    print("Parsing weapon profiles...")
    weapons_map = {}
    w_reader = csv.DictReader(io.StringIO(wargear_csv), delimiter='|')
    for row in w_reader:
        ds_id = row['datasheet_id']
        if not row['name']:
            continue
        # Filter out options that aren't weapons (must have attack/damage attributes)
        if not row['A'] and not row['S']:
            continue
        if ds_id not in weapons_map:
            weapons_map[ds_id] = []
        weapons_map[ds_id].append({
            "name": row['name'],
            "description": row['description'],
            "range": row['range'],
            "type": row['type'],
            "a": row['A'],
            "bs": row['BS_WS'],
            "s": row['S'],
            "ap": row['AP'],
            "d": row['D']
        })

    # 5. Join everything under the main Datasheets
    print("Joining tables into final unit datasheets...")
    results = []
    ds_reader = csv.DictReader(io.StringIO(datasheets_csv), delimiter='|')
    for row in ds_reader:
        ds_id = row['id']
        faction_name = faction_map.get(row['faction_id'], "Unknown Faction")

        models = models_map.get(ds_id, [])
        weapons = weapons_map.get(ds_id, [])

        if not models:
            continue

        # Use primary model for basic squad parameters
        primary_model = models[0]

        # Clean HTML tags out of description fields
        clean_loadout = re.sub('<[^<]+?>', '', row['loadout']) if row['loadout'] else "Standard wargear."

        entry = {
            "name": row['name'],
            "content_type": "unit",
            "description": f"A squad profile of the {faction_name}. Default loadout: {clean_loadout}",
            "extra_data": {
                "faction": faction_name,
                "role": row['role'],
                "m": primary_model["m"],
                "t": primary_model["t"],
                "sv": primary_model["sv"],
                "w": primary_model["w"],
                "ld": primary_model["ld"],
                "oc": primary_model["oc"],
                "invulnerable": primary_model["invulnerable"],
                "weapons": weapons,
                "source_url": row['link']
            }
        }
        results.append(entry)

    out_path = os.path.join(DATA_DIR, "units.json")
    save_to_json(results, out_path)
    print(f"✓ Pipeline complete! Processed {len(results)} total unit profiles.")


if __name__ == "__main__":
    run()