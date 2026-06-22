# scrapers/base.py
from curl_cffi import requests  # <-- Changed from standard requests
import json
import time
import os
import random

# Headers are still good to have, but curl_cffi does the heavy lifting
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_DELAY = 2.0  # Bumped up slightly to be safe

def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            # Added impersonate="chrome" to mimic real browser TLS fingerprints
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

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            # If fetching 5etools from GitHub, standard requests is fine, but chrome impersonation works here too
            response = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"  Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(REQUEST_DELAY * 2)
            else:
                print(f"  Giving up on {url}")
                return None

# Keep your save_to_json, load_json, deduplicate, and polite_delay functions exactly the same!
def save_to_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filepath}")

def polite_delay():
    jittered_delay = REQUEST_DELAY + random.uniform(0.5, 2.5)
    time.sleep(jittered_delay)