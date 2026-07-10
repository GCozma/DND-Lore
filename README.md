# 🔮 Lore Oracle Portal
An AI-powered tabletop gaming portal hosting a **Dungeons & Dragons 5e Campaign Companion** and a **Warhammer 40k 10th Edition Tactician & Battle Simulator**. 
Ask questions about spells, units, faction lore, items, and rules — or run interactive, turn-by-turn combat simulations — utilizing a Retrieval-Augmented Generation (RAG) pipeline grounded in scraped gaming database content.
---
## What It Does
### 🐉 D&D 5e Oracle
* **Explain Mode** — Get rules and lore grounded in real data:
  > *"What does Fireball do?"*
  > *"Tell me about Aboleths."*
* **Combat Simulator** — Run turn-by-turn D&D encounters where the AI tracks Initiative, rolls monster attacks, and pauses to ask for your d20 rolls.
* **DM Mode Toggle** — Reveal hidden monster stats, CR ratings, vulnerabilities, and generate tactical plot hooks.
### ⚔️ Warhammer 40k Oracle
* **Lore Mode** — Deep gothic narrative lore regarding the far future:
  > *"Who is the Emperor of Mankind?"*
  > *"Tell me about the Horus Heresy."*
* **Tactician Mode** — Build lists, view stats, and compare weapon profiles across all 10th Edition factions using Markdown tables.
* **Battle Simulator** — Simulate skirmish combat turn-by-turn using exact 10th Edition rules (Hit rolls vs BS/WS, Wound rolls vs S/T, Armour Saves modified by AP, and Wounds tracking).
---
## How It Works
This project uses a dual-engine **RAG (Retrieval-Augmented Generation)** pipeline:


Scraped D&D / WH40K Content
               ↓
SQLite (flat relational search) ChromaDB (vector embeddings search) ↓ [Hybrid Engine Selection] /
↓ ↓ (Online - Free Cloud) (Offline - Local) Gemini 1.5 Flash API Ollama + Llama 3.1 (Google GenAI) (Runs on your machine) \ / \ / ↓ ↓ Grounded, Mathematically Accurate Output



If you configure your free Gemini API key, the portal connects to Google's cloud server to run calculations instantly. If you go offline, it automatically falls back to your local GPU-accelerated Ollama models.
---
## Data Collected & Indexed
### D&D 5e Archives
| Content Type | Source | Count |
|---|---|---|
| Spells | 5etools | 449 |
| Monsters | 5etools | 842 |
| Magic Items | 5etools | 1819 |
| Classes & Subclasses | 5etools | 170 |
| Deities | 5etools | 322 |
| Regions | Forgotten Realms Wiki | 123 |
| Rules & Mechanics | 5etools | 223 |
### Warhammer 40K Archives
| Content Type | Source | Count |
|---|---|---|
| Unit Datasheets | Wahapedia CSV exports | 1711 |
| Core Factions | Wahapedia CSV exports | 8 |
| Narrative Lore | Lexicanum Wiki | 21 |
| **Combined Database Rows** | | **5688** |
---
## Requirements
- Python 3.11+
- [Ollama](https://ollama.com) with `llama3.1` pulled (for offline fallback)
- AMD GPU with ROCm **or** NVIDIA GPU with CUDA
- ~12GB disk space (models + database + vector index files)
- Optional: A free **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/) for the cloud engine.
---
## Installation
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/lore-oracle-portal.git
cd lore-oracle-portal
# Since the project uses uv, install dependencies in your virtual environments:
# For D&D
cd Lore_oracle/
uv pip install -r pyproject.toml
uv pip install google-genai
# For Warhammer
cd ../Warhammer_oracle/
uv pip install -r pyproject.toml
uv pip install google-genai
First-Time Setup
Run the compilers in order inside both projects to build your relational databases and ChromaDB vector indexes:

bash


# 1. Compile D&D Database
cd ../Lore_oracle/
python scrapers/build_database.py
python scrapers/build_embeddings.py
# 2. Compile Warhammer Database
cd ../Warhammer_oracle/
python Scrappers/wh40k_units.py
python Scrappers/wh40k_lore.py
python Scrappers/build_database.py
python Scrappers/build_embeddings.py
Running the App
Create a .env file inside Master_Oracle/ and paste your Gemini API key:
text


GEMINI_API_KEY="your-free-gemini-api-key"
Launch the portal using the automated startup script:
bash


cd ../Master_Oracle/
chmod +x start_portal.sh
./start_portal.sh
Open your browser at http://localhost:8501.

AMD GPU Setup (Arch Linux)
If Ollama defaults to CPU instead of your AMD GPU:

bash


# Install ROCm variant
sudo pacman -S ollama-rocm
# Find your GPU's gfx version
/opt/rocm/bin/rocminfo | grep gfx
# Create override (replace X.Y.Z with your gfx version, e.g. 10.3.0)
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo nano /etc/systemd/system/ollama.service.d/override_gfx_version.conf
Paste:

ini


[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=X.Y.Z"
bash


sudo systemctl daemon-reload
sudo systemctl restart ollama
Verify with ollama ps — should show 100% GPU.

Project Structure


Master_Oracle/
├── homepage.py                ← Streamlit portal landing page
├── start_portal.sh            ← Automated startup script
├── .env                       ← Secret file storing API Keys (ignored by git)
├── .gitignore                 ← Tells Git what files to ignore
├── pages/
│   ├── dnd_oracle.py          ← D&D sub-app wrapper
│   └── wh40k_oracle.py        ← WH40K sub-app wrapper
│
├── Lore_oracle/               # D&D Backend Files
│   ├── scrapers/
│   │   ├── build_database.py
│   │   ├── build_embeddings.py
│   │   └── query_lore.py
│   └── data/
│
└── Warhammer_oracle/          # Warhammer 40k Backend Files
    ├── Scrappers/
    │   ├── build_database.py
    │   ├── build_embeddings.py
    │   └── query_lore.py
    └── data/
Roadmap
 Warhammer 40K database RAG pipeline (Lexicanum & Wahapedia)
 Cloudflare Tunnel implementation for remote access
 Cloud hybrid fallback logic for logical accuracy (Gemini)
 Add Morale and Battle-shock test logic to the WH40K simulator
 Implement local session history export to Markdown logs
 Add Streamlit password protection for public deployments
Built With
Python
Streamlit — Web Interface
SQLite — Relational DB
ChromaDB — Semantic Vector Search
Google GenAI SDK — Cloud reasoning
Ollama — Local inference fallback
Wahapedia — Warhammer 40k 10th Ed database source
5etools — D&D 5e database source
Forgotten Realms Wiki — Region lore source
Lexicanum Wiki — WH40K lore source
