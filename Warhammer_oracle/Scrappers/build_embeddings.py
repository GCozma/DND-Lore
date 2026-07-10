# warhammer_oracle/Scrappers/build_embeddings.py
import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

from Scrappers.constants import DB_PATH, CHROMA_PATH

def load_all_rows():
    """Pulls searchable narrative descriptions from SQLite."""
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
    print(f"  {len(rows)} rows will be embedded")

    if not rows:
        print("No narrative rows found. Please build the SQLite database first.")
        return

    print("\nLoading embedding model (~80MB)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("\nConnecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="lore")

    ids = []
    documents = []
    metadatas = []

    for row_id, name, content_type, description in rows:
        ids.append(str(row_id))
        # Embed name + description together to preserve name context
        documents.append(f"{name}: {description}")
        metadatas.append({"name": name, "content_type": content_type})

    print(f"\nEncoding {len(documents)} documents...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    print("\nStoring in ChromaDB...")
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