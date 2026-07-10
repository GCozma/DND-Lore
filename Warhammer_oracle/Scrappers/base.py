# warhammer_oracle/Scrappers/base.py
from curl_cffi import requests
import json
import time
import os
import random

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_DELAY = 2.0

def fetch_page(url, retries=3):
    """Fetches raw HTML from a URL using browser impersonation."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(REQUEST_DELAY * 2)
            else:
                print(f"  Giving up on {url}")
                return None

def save_to_json(data, filepath):
    """Saves a list/dictionary of data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filepath}")

def polite_delay():
    """Applies a polite random delay between requests to avoid rate limits."""
    delay = REQUEST_DELAY + random.uniform(0.5, 2.5)
    time.sleep(delay)