# scrapers/dnd_spells.py
from scrapers.base import fetch_page, save_to_json, load_json, polite_delay

from bs4 import BeautifulSoup
import os

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_LIST     = os.path.join(ROOT, "data", "dnd", "spells_list.json")
OUTPUT_DETAILED = os.path.join(ROOT, "data", "dnd", "spells.json")

BASE_DOMAIN = "https://www.dndbeyond.com"
SPELL_LIST_URL = "https://www.dndbeyond.com/spells?page={}"


def parse_spell_list(html):
    soup = BeautifulSoup(html, "html.parser")
    spells = []
    seen_names = set()

    name_spans = soup.find_all("span", class_="name")
    for span in name_spans:
        link_tag = span.find("a")
        if link_tag:
            name = link_tag.get_text(strip=True)
            url = link_tag["href"]
            if name not in seen_names:
                seen_names.add(name)
                spells.append({"name": name, "url": url})

    return spells


def parse_spell_detail(html, spell_name, spell_url):
    soup = BeautifulSoup(html, "html.parser")

    # Every entry starts with these shared base fields
    spell = {
        "name":         spell_name,
        "url":          spell_url,
        "universe":     "dnd",
        "source":       "dndbeyond",
        "content_type": "spell",      # ← new field, consistent across all types
        "description":  ""
    }

    # Stats
    statblock = soup.find("div", class_="ddb-statblock-spell")
    if statblock:
        items = statblock.find_all("div", class_="ddb-statblock-item")
        for item in items:
            label_tag = item.find("div", class_="ddb-statblock-item-label")
            value_tag = item.find("div", class_="ddb-statblock-item-value")
            if label_tag and value_tag:
                label = label_tag.get_text(strip=True).lower().replace(" ", "_")
                value = value_tag.get_text(strip=True)
                spell[label] = value

    # Description
    description_div = soup.find("div", class_="more-info-content")
    if description_div:
        paragraphs = description_div.find_all("p")
        spell["description"] = "\n".join(
            p.get_text(strip=True) for p in paragraphs
        )

    # Classes
    classes_tag = soup.find("p", class_="available-for")
    if classes_tag:
        class_spans = classes_tag.find_all("span", class_="class-tag")
        spell["classes"] = [s.get_text(strip=True) for s in class_spans]

    return spell


def scrape_spell_list():
    """Phase 1 — collect all spell names and URLs."""
    print("=== PHASE 1: Scraping spell list ===")
    all_spells = []
    seen_names = set()
    current_page = 1
    empty_streak = 0

    while True:
        url = SPELL_LIST_URL.format(current_page)
        print(f"Fetching page {current_page}...")

        html = fetch_page(url)
        if not html:
            break

        spells = parse_spell_list(html)
        new_spells = [s for s in spells if s["name"] not in seen_names]

        if len(new_spells) == 0:
            empty_streak += 1
            if empty_streak >= 3:
                print("Reached the end!")
                break
        else:
            empty_streak = 0
            for s in new_spells:
                seen_names.add(s["name"])
            all_spells.extend(new_spells)
            print(f"  → {len(new_spells)} new spells (total: {len(all_spells)})")

        current_page += 1
        polite_delay()

    save_to_json(all_spells, OUTPUT_LIST)
    return all_spells


def scrape_spell_details(spell_list):
    """Phase 2 — scrape full details for each spell."""
    print("\n=== PHASE 2: Scraping spell details ===")
    detailed_spells = []

    for i, spell in enumerate(spell_list):
        full_url = BASE_DOMAIN + spell["url"]
        print(f"[{i+1}/{len(spell_list)}] {spell['name']}")

        html = fetch_page(full_url)
        if html:
            detail = parse_spell_detail(html, spell["name"], spell["url"])
            detailed_spells.append(detail)

        if (i + 1) % 50 == 0:
            save_to_json(detailed_spells, OUTPUT_DETAILED)
            print(f"  ✓ Checkpoint at {i+1}")

        polite_delay()

    save_to_json(detailed_spells, OUTPUT_DETAILED)
    return detailed_spells


def run():
    """Run the full spell scraper pipeline."""
    spell_list = scrape_spell_list()
    scrape_spell_details(spell_list)
    print("\nSpell scraping complete!")