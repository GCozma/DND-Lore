import os
from bs4 import BeautifulSoup
from scrapers.base import fetch_page, polite_delay, save_to_json
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "dnd", "regions.json")

WIKI_BASE = "https://forgottenrealms.fandom.com"

REGION_PAGES = [
    "/wiki/Baldur%27s_Gate",
    "/wiki/Waterdeep",
    "/wiki/Sword_Coast",
    "/wiki/Neverwinter",
    "/wiki/Underdark",
    "/wiki/Amn",
    "/wiki/Anauroch",
    "/wiki/Calimshan",
    "/wiki/Chult",
    "/wiki/Cormyr",
    "/wiki/Dalelands",
    "/wiki/Damara",
    "/wiki/Elfharrow",
    "/wiki/Evermeet",
    "/wiki/High_Forest",
    "/wiki/Hordelands",
    "/wiki/Icewind_Dale",
    "/wiki/Impiltur",
    "/wiki/Lantan",
    "/wiki/Moonshae_Isles",
    "/wiki/Mulhorand",
    "/wiki/Narfell",
    "/wiki/Rashemen",
    "/wiki/Sembia",
    "/wiki/Silver_Marches",
    "/wiki/Tethyr",
    "/wiki/Thay",
    "/wiki/Moonsea",
    "/wiki/Unapproachable_East",
    "/wiki/Unther",
    "/wiki/Vaasa",
    "/wiki/Vast",
    "/wiki/Vilhon_Reach",
    "/wiki/Western_Heartlands"
]


def strip_citations(soup_element):
    """Removes footnote reference markers completely."""
    for citation in soup_element.find_all("sup", class_="reference"):
        citation.decompose()
    return soup_element


def parse_description(soup):
    """
    Extracts the main article text safely, avoiding nested elements
    inside infoboxes or tables while ensuring deep nested paragraphs are caught.
    """
    content = soup.find("div", class_="mw-parser-output")
    if not content:
        return ""

    strip_citations(content)
    paragraphs = content.find_all("p", recursive=False)

    texts = []
    for p in paragraphs:
        text = p.get_text(separator=" ", strip=True)

        if not text or len(text) <= 20:
            continue
        if text.startswith("Disclaimer:"):
            continue

        texts.append(text)

    description = "\n\n".join(texts)

    # Collapse any double spaces created by the separator
    description = re.sub(r' {2,}', ' ', description)

    return description


def parse_infobox(soup):
    """
    Extracts label/value pairs from Fandom's portable infobox component.
    """
    infobox = soup.find("aside", class_="portable-infobox")
    if not infobox:
        return {}

    strip_citations(infobox)

    facts = {}
    data_items = infobox.find_all("div", class_="pi-data")

    for item in data_items:
        label_tag = item.find("h3", class_="pi-data-label")
        value_tag = item.find("div", class_="pi-data-value")

        if label_tag and value_tag:
            label = label_tag.get_text(strip=True)

            for br in value_tag.find_all("br"):
                br.replace_with(", ")

            value = value_tag.get_text(separator=" ", strip=True)
            value = re.sub(r' {2,}', ' ', value)
            facts[label] = value

    return facts


def parse_region(html, name, url):
    soup = BeautifulSoup(html, "html.parser")

    return {
        "name": name,
        "universe": "dnd",
        "source": "forgottenrealms_wiki",
        "content_type": "region",
        "url": url,
        "description": parse_description(soup),
        "facts": parse_infobox(soup)
    }


def run():
    all_regions = []

    for page_path in REGION_PAGES:
        url = WIKI_BASE + page_path
        # Decode the URL encoding back into human readable strings
        name = page_path.split("/")[-1].replace("_", " ").replace("%27", "'")

        print(f"Scraping {name}...")
        html = fetch_page(url)

        if html:
            region = parse_region(html, name, url)
            all_regions.append(region)
            print(f"  ✓ {len(region['description'])} chars, {len(region['facts'])} facts")
        else:
            print(f"  ✗ Failed to fetch {name}")

        polite_delay()

    save_to_json(all_regions, OUTPUT)
    print(f"\nDone! {len(all_regions)} regions saved.")


if __name__ == "__main__":
    run()