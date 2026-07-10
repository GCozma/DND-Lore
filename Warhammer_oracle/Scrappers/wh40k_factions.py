import re
from bs4 import BeautifulSoup
from sympy import content

from Scrappers.base import fetch_page, save_to_json, polite_delay
from Scrappers.constants import LEXICANUM_BASE_URL, DATA_DIR, os

FACTIONS = [
    {"name": "Space Marines", "slug": "Space_Marines"},
    {"name": "Necrons", "slug": "Necrons"},
    {"name": "Orks", "slug": "Orks"},
    {"name": "Tyranids", "slug": "Tyranids"},
    {"name": "Aeldari", "slug": "Eldar"},
    {"name": "Chaos Space Marines", "slug": "Chaos_Space_Marines"},
    {"name": "Astra Militarum", "slug": "Imperial_Guard"},
    {"name": "Tau Empire", "slug": "T%27au_Empire"}
]

def clean_wiki_text(text):
   """Clean up wiki markers, citations and extra spacing"""
   text = re.sub(r'\[\d+[a-zA-Z]?\]', '', text)
   text=re.sub(r'\s+',' ',text)
   return text.strip()

def scrape_faction_lore(slug):
    """Scrapes the main introduction paragraphs from a Lexicanum page"""
    url=f"{LEXICANUM_BASE_URL}{slug}"
    print(f'Scraping faction: {slug} from {url}...')

    html=fetch_page(url)
    if not html:
        return ""

    soup=BeautifulSoup(html, 'html.parser')
    content_div=soup.find('div', {'id':'mw-content-text'})
    if not content_div:
        return ""

    paragraphs = []
    # Loop through direct children of content text
    for child in content_div.find_all(["p", "h2", "h3"], recursive=True):
        # Stop scraping if we reach references or sources section
        if child.name in ["h2", "h3"]:
            header_text = child.get_text().lower()
            if any(term in header_text for term in ["source", "see also", "reference", "gallery", "translation"]):
                break
            continue
        if child.name=='p':
            para_text=clean_wiki_text(child.get_text())
            if para_text and len(para_text) >40:
                paragraphs.append(para_text)

    #Return first 6 paragraphs as the core lore summary
    return "\n\n".join(paragraphs[:6])

def run():
    results = []
    for faction in FACTIONS:
        lore = scrape_faction_lore(faction["slug"])
        if lore:
            entry = {
                "name": faction["name"],
                "content_type": "faction",
                "description": lore,
                "extra_data": {
                    "source_url": f"{LEXICANUM_BASE_URL}{faction['slug']}"
                }
            }
            results.append(entry)
        polite_delay()
    out_path = os.path.join(DATA_DIR, "factions.json")
    save_to_json(results, out_path)
if __name__ == "__main__":
    run()

