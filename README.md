# 🐉 Lore Oracle

A local AI-powered D&D lore assistant and campaign builder. Ask questions about spells, monsters, items, classes, deities, and regions — or generate custom encounters, NPCs, and plot hooks — all grounded in real, scraped D&D content and running entirely on your own machine.

---

## What It Does

**Explain Mode** — ask about any D&D topic and get an answer grounded in real lore data:
> *"What does Fireball do?"*
> *"Tell me about Aboleths."*
> *"What's the history of Baldur's Gate?"*

**Campaign Mode** — generate original content inspired by real lore:
> *"Generate an encounter for a level 3 party near the Underdark."*
> *"Create an NPC merchant in Waterdeep with a secret."*
> *"Give me a plot hook involving the Flaming Fist."*

---

## How It Works

This project uses a **RAG (Retrieval-Augmented Generation)** pipeline:

```
Scraped D&D Content
        ↓
SQLite (structured storage + exact search)
ChromaDB (vector embeddings + semantic search)
        ↓
Relevant lore retrieved for your question
        ↓
Ollama + Llama 3.1:8b (local LLM, GPU-accelerated)
        ↓
Grounded, accurate answer
```

No data leaves your machine. No API keys. No costs.

---

## Data Collected

| Content Type | Source     | Count |
|---|---|---|
| Spells       | 5etools    | 449   |
| Monsters     | 5etools    | 842   |
| Magic Items  | 5etools    | 1819  |
| Classes      | 5etools    | 13    |
| Subclasses   | 5etools    | 157   |
| Deities      | 5etools    | 322   |
| Regions      | Forgotten Realms Wiki | 34 |
| **Total**    |            | **3636** |

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) with `llama3.1:8b` pulled
- AMD GPU with ROCm **or** NVIDIA GPU with CUDA (CPU works but is slow)
- ~10GB disk space (model + data + embeddings)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/lore-oracle.git
cd lore-oracle

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull the LLM
ollama pull llama3.1:8b
```

---

## First-Time Setup

Run these once, in order, to build the database and embeddings:

```bash
# 1. Collect all D&D data (takes 20-30 mins — makes many web requests)
python main.py

# 2. Build the SQLite database
python scrapers/build_database.py

# 3. Generate vector embeddings (takes a few minutes)
python scrapers/build_embeddings.py
```

---

## Running the App

```bash
# Make sure Ollama is running
sudo systemctl start ollama

# Launch the web interface
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## AMD GPU Setup (Arch Linux)

If Ollama defaults to CPU instead of your AMD GPU:

```bash
# Install ROCm variant
sudo pacman -S ollama-rocm

# Find your GPU's gfx version
/opt/rocm/bin/rocminfo | grep gfx

# Create override (replace X.Y.Z with your gfx version, e.g. 10.3.0)
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo nano /etc/systemd/system/ollama.service.d/override_gfx_version.conf
```

Paste:
```ini
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=X.Y.Z"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify with `ollama ps` — should show `100% GPU`.

---

## Project Structure

```
lore_oracle/
├── app.py                    ← Streamlit web interface
├── main.py                   ← runs all scrapers
├── requirements.txt
├── scrapers/
│   ├── base.py               ← shared fetch/save utilities
│   ├── tag_cleaner.py        ← cleans 5etools {@tag} markup
│   ├── dnd_spells_5e.py      ← spell scraper (5etools)
│   ├── dnd_monsters.py       ← monster scraper (5etools)
│   ├── dnd_items.py          ← magic item scraper (5etools)
│   ├── dnd_classes.py        ← class/subclass scraper (5etools)
│   ├── dnd_deities.py        ← deity scraper (5etools)
│   ├── dnd_regions.py        ← region scraper (Forgotten Realms Wiki)
│   ├── build_database.py     ← loads JSON into SQLite
│   ├── build_embeddings.py   ← generates ChromaDB vector embeddings
│   └── query_lore.py         ← interactive CLI + ask() function
└── data/
    ├── lore_oracle.db        ← SQLite database (generated, not in repo)
    ├── chroma_db/            ← ChromaDB embeddings (generated, not in repo)
    └── dnd/
        ├── spells.json
        ├── monsters.json
        ├── items.json
        ├── classes.json
        ├── subclasses.json
        ├── deities.json
        └── regions.json
```

---

## Roadmap

- [ ] Warhammer 40K content (Lexicanum scraper)
- [ ] Cloudflare Tunnel for remote access
- [ ] Campaign session notes (persistent memory)
- [ ] More regions and NPC lore

---

## Built With

- [Python](https://python.org)
- [Streamlit](https://streamlit.io) — web interface
- [SQLite](https://sqlite.org) — structured storage
- [ChromaDB](https://trychroma.com) — vector search
- [sentence-transformers](https://sbert.net) — text embeddings
- [Ollama](https://ollama.com) — local LLM inference
- [5etools](https://5e.tools) — D&D structured data source
- [Forgotten Realms Wiki](https://forgottenrealms.fandom.com) — region lore
- [curl_cffi](https://github.com/yifeikong/curl_cffi) — browser-impersonating HTTP client

---

## License

Personal/educational use. D&D content belongs to Wizards of the Coast. 5etools data is community-maintained fan content. This project does not redistribute copyrighted material — it scrapes and indexes publicly available reference data for personal use only.
