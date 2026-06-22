# scrapers/build_embeddings.py
import sqlite3
import os
import chromadb
from sentence_transformers import SentenceTransformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "lore_oracle.db")
CHROMA_PATH = os.path.join(ROOT, "data", "chroma_db")


def load_all_rows():
    """
    Pulls every row from SQLite that we want to make searchable.
    Returns id, name, content_type, and description for each.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, content_type, description
        FROM content
        WHERE description IS NOT NULL AND description != ''
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def run():
    print("Loading rows from SQLite...")
    rows = load_all_rows()
    print(f"  {len(rows)} rows have descriptions and will be embedded")

    print("\nLoading embedding model (first run downloads it, ~80MB)...")
    # all-MiniLM-L6-v2 is small, fast, and good enough for this use case
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("\nConnecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # get_or_create_collection: like CREATE TABLE IF NOT EXISTS,
    # but for a vector collection instead of a SQL table
    collection = client.get_or_create_collection(name="lore")

    # Prepare the data in the shape ChromaDB expects:
    # parallel lists — ids[i] goes with documents[i] goes with metadatas[i]
    ids = []
    documents = []
    metadatas = []

    for row_id, name, content_type, description in rows:
        # ChromaDB ids must be strings, our SQLite ids are integers
        ids.append(str(row_id))

        # We embed name + description together — gives the model
        # both the identity and the meaning of the entry
        documents.append(f"{name}: {description}")

        # Metadata lets us filter results later (e.g. only monsters)
        # without needing to look anything up in SQLite first
        metadatas.append({"name": name, "content_type": content_type})

    print(f"\nEmbedding {len(documents)} documents...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    print("\nStoring in ChromaDB...")
    # ChromaDB has a batch size limit, so we insert in chunks
    BATCH_SIZE = 500
    for i in range(0, len(ids), BATCH_SIZE):
        batch_end = i + BATCH_SIZE
        collection.upsert(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        print(f"  Stored {min(batch_end, len(ids))}/{len(ids)}")

    print(f"\nDone! {collection.count()} embeddings stored in ChromaDB.")


if __name__ == "__main__":
    run()