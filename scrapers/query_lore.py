# scrapers/ask_lore.py
import sqlite3
import os
import json
import chromadb
import ollama
from sentence_transformers import SentenceTransformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lore_oracle.db")
CHROMA_PATH = os.path.join(ROOT, "data", "chroma_db")

MODEL_NAME = "llama3.1:8b"

# Two different "personalities" for the same underlying pipeline.
# The retrieval (search) stays identical — only the instructions change.
PROMPTS = {
    "explain": """You are a D&D lore assistant. Use ONLY the reference material below to answer the question. If the material doesn't fully answer the question, say so honestly rather than making things up.

REFERENCE MATERIAL:
{context}

QUESTION: {question}

ANSWER:""",

    "campaign": """You are a creative D&D Dungeon Master's assistant helping build campaign content. Use the reference material below as INSPIRATION and GROUNDING — stay consistent with this established lore, but you may creatively extend it to fulfill the request (inventing specific NPCs, encounters, or details where the lore doesn't specify them).

REFERENCE MATERIAL:
{context}

REQUEST: {question}

RESPONSE:"""
}


def get_full_entry(cursor, row_id):
    cursor.execute("SELECT * FROM content WHERE id = ?", (row_id,))
    return cursor.fetchone()


def search(query_text, n_results=5, content_type_filter=None, model=None):
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name="lore")

    query_embedding = model.encode([query_text]).tolist()
    where_clause = {"content_type": content_type_filter} if content_type_filter else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_clause
    )

    matched_ids = results["ids"][0]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    entries = []
    for row_id in matched_ids:
        row = get_full_entry(cursor, int(row_id))
        _, name, universe, source, content_type, description, extra_data = row
        entries.append({
            "name": name,
            "content_type": content_type,
            "description": description,
            "extra_data": json.loads(extra_data)
        })

    conn.close()
    return entries


def format_context(entries, max_chars=2000):
    blocks = []
    for entry in entries:
        description = entry["description"]
        if len(description) > max_chars:
            description = description[:max_chars] + "... [truncated]"

        block = f"## {entry['name']} ({entry['content_type']})\n"
        block += f"{description}\n"
        if entry["extra_data"]:
            block += f"Details: {json.dumps(entry['extra_data'])}\n"
        blocks.append(block)

    return "\n---\n".join(blocks)


def ask(question, mode="explain", n_results=5, content_type_filter=None, embed_model=None):
    entries = search(question, n_results=n_results,
                      content_type_filter=content_type_filter, model=embed_model)
    context = format_context(entries)

    prompt_template = PROMPTS.get(mode, PROMPTS["explain"])
    prompt = prompt_template.format(context=context, question=question)

    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={"num_ctx": 8192}
    )

    return response["response"], entries


def interactive_loop():
    """
    A simple chat-style loop. Type a question, get an answer.
    Type 'mode campaign' or 'mode explain' to switch modes.
    Type 'quit' or 'exit' to stop.
    """
    print("=== LORE ORACLE ===")
    print("Loading embedding model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    mode = "explain"
    print(f"\nReady. Mode: {mode}")
    print("Commands: 'mode explain' | 'mode campaign' | 'quit'\n")

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() in ("quit", "exit"):
            print("Farewell, adventurer.")
            break

        if question.lower() == "mode explain":
            mode = "explain"
            print(f"→ Switched to explain mode\n")
            continue

        if question.lower() == "mode campaign":
            mode = "campaign"
            print(f"→ Switched to campaign mode\n")
            continue

        print("\nSearching and thinking...\n")
        answer, entries = ask(question, mode=mode, embed_model=embed_model)

        print(f"Oracle [{mode}]: {answer}\n")
        sources = ", ".join(e["name"] for e in entries)
        print(f"(Sources: {sources})\n")


if __name__ == "__main__":
    interactive_loop()