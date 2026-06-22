# main.py
from scrapers import dnd_spells_5e
from scrapers import dnd_monsters
from scrapers import dnd_items
from scrapers import dnd_classes
from scrapers import dnd_deities
from scrapers import dnd_regions

# Later you'll add:
# from scrapers import dnd_monsters
# from scrapers import dnd_items

if __name__ == "__main__":
    print("=== LORE ORACLE — Data Collection ===\n")
    dnd_spells_5e.run()
    dnd_monsters.run()
    dnd_items.run()
    dnd_classes.run()
    dnd_deities.run()
    dnd_regions.run()
    