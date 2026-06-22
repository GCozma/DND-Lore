# app.py
import streamlit as st
from sentence_transformers import SentenceTransformer
from scrapers.query_lore import ask

st.set_page_config(page_title="Lore Oracle", page_icon="🐉")

st.title("🐉 Lore Oracle")
st.caption("Your D&D campaign lore assistant")

# ── Load the embedding model ONCE, not on every interaction ────────────────
# Streamlit re-runs your whole script top-to-bottom on every user action.
# Without caching, we'd reload this slow model every single time.
@st.cache_resource
def load_embed_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embed_model()

# ── Sidebar for mode selection ──────────────────────────────────────────────
mode = st.sidebar.radio("Mode", ["explain", "campaign"])
st.sidebar.caption(
    "**Explain**: ask about lore, spells, monsters, items.\n\n"
    "**Campaign**: generate encounters, NPCs, plot hooks."
)

# ── Chat history ─────────────────────────────────────────────────────────────
# st.session_state persists data across reruns within the same browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg:
            st.caption(f"Sources: {msg['sources']}")

# ── Input box ─────────────────────────────────────────────────────────────
question = st.chat_input("Ask the Oracle...")

if question:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Get and show the answer
    with st.chat_message("assistant"):
        with st.spinner("Searching and thinking..."):
            answer, entries = ask(question, mode=mode, embed_model=embed_model)

        st.write(answer)
        sources = ", ".join(e["name"] for e in entries)
        st.caption(f"Sources: {sources}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })