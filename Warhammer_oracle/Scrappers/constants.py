# warhammer_oracle/Scrappers/constants.py
import os

# ── Path Constants ────────────────────────────────────────────────────────────
# Points to the root project directory (Warhammer_oracle/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "warhammer")
DB_PATH = os.path.join(DATA_DIR, "warhammer_oracle.db")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ── Scraper Target URLs ───────────────────────────────────────────────────────
# Lexicanum Wiki URLs (MediaWiki structure)
LEXICANUM_BASE_URL = "https://wh40k.lexicanum.com/wiki/"

# Wahapedia Faction & Rules Endpoint
WAHAPEDIA_CSV_BASE = "https://wahapedia.ru/wh40k10ed/"