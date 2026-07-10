# warhammer_oracle/Scrappers/wh40k_lore.py
import re
from bs4 import BeautifulSoup
from Scrappers.base import fetch_page, save_to_json, polite_delay
from Scrappers.constants import LEXICANUM_BASE_URL, DATA_DIR, os

LORE_TOPICS = [
    # ── Core Imperium & Humanity ──
    {"name": "Emperor of Mankind", "slug": "Emperor_of_Mankind"},
    {"name": "Imperium of Man", "slug": "Imperium_of_Man"},
    {"name": "Golden Throne", "slug": "Golden_Throne"},
    {"name": "Adeptus Mechanicus", "slug": "Adeptus_Mechanicus"},
    {"name": "High Lords of Terra", "slug": "High_Lords_of_Terra"},

    # ── Legions & Military History ──
    {"name": "Space Marine Legions", "slug": "Space_Marine_Legion"},
    {"name": "Primarch", "slug": "Primarch"},
    {"name": "Great Crusade", "slug": "Great_Crusade"},
    {"name": "Horus Heresy", "slug": "Horus_Heresy"},
    {"name": "Black Crusade", "slug": "Black_Crusade"},

    # ── Chaos & The Warp ──
    {"name": "Chaos", "slug": "Chaos"},
    {"name": "The Warp", "slug": "Warp"},
    {"name": "Chaos Gods", "slug": "Gods_of_Chaos"},
    {"name": "Eye of Terror", "slug": "Eye_of_Terror"},

    # ── Xenos Factions & Ancient History ──
    {"name": "Necrons", "slug": "Necron"},
    {"name": "War in Heaven", "slug": "War_in_Heaven_(Necron)"},
    {"name": "C'tan", "slug": "C%27tan"},
    {"name": "Orks", "slug": "Ork"},
    {"name": "Eldar", "slug": "Eldar"},
    {"name": "Tyranids", "slug": "Tyranid"},
    {"name": "Webway", "slug": "Webway"}
]


def clean_wiki_text(text):
    text = re.sub(r'\[\d+[a-zA-Z]?\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_lore_topic(slug):
    url = f"{LEXICANUM_BASE_URL}{slug}"
    print(f"Scraping lore topic: {slug} from {url}...")

    html = fetch_page(url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        return ""

    paragraphs = []
    for child in content_div.find_all(["p", "h2", "h3"]):
        if child.name in ["h2", "h3"]:
            header_text = child.get_text().lower()
            if any(term in header_text for term in
                   ["source", "see also", "reference", "gallery", "weapon", "equipment"]):
                break
            continue

        if child.name == "p":
            para_text = clean_wiki_text(child.get_text())
            if para_text and len(para_text) > 40:
                paragraphs.append(para_text)

    # Return up to 8 paragraphs for deep context
    return "\n\n".join(paragraphs[:8])


def run():
    results = []
    for topic in LORE_TOPICS:
        description = scrape_lore_topic(topic["slug"])
        if description:
            entry = {
                "name": topic["name"],
                "content_type": "lore",
                "description": description,
                "extra_data": {
                    "topic": topic["name"],
                    "source_url": f"{LEXICANUM_BASE_URL}{topic['slug']}"
                }
            }
            results.append(entry)
            polite_delay()

    out_path = os.path.join(DATA_DIR, "lore.json")
    save_to_json(results, out_path)


if __name__ == "__main__":
    run()