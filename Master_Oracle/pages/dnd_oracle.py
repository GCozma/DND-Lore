# Master_Oracle/pages/dnd_oracle.py
import sys
import os
import streamlit as st
from sentence_transformers import SentenceTransformer

# 1. Dynamically link the existing D&D project modules
DND_PROJECT_ROOT = "/home/george/PycharmProjects/Lore_oracle/lore_oracle"
sys.path.insert(0, DND_PROJECT_ROOT)

from scrapers.query_lore import get_oracle_response, get_all_known_names

# ── Streamlit UI Setup ────────────────────────────────────────────────────────
st.set_page_config(page_title="D&D Lore Oracle", page_icon="🐉", layout="wide")

st.title("🐉 D&D Lore Oracle")
st.caption("Your integrated D&D campaign lore and worldbuilding companion")


# Load Resources
@st.cache_resource
def load_resources():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    names = get_all_known_names()
    return model, names


embed_model, known_names = load_resources()

# Session State Initializations
if "chat_history_dnd" not in st.session_state:
    st.session_state.chat_history_dnd = []
if "dm_mode" not in st.session_state:
    st.session_state.dm_mode = False
if "combat_mode_dnd" not in st.session_state:
    st.session_state.combat_mode_dnd = False

# Sidebar Toggles
with st.sidebar:
    st.markdown("### D&D Oracle Settings")

    # Visual Engine Status Indicator
    if os.environ.get("GEMINI_API_KEY"):
        st.success("☁️ Engine: Gemini Cloud")
    else:
        st.warning("🖥️ Engine: Local Ollama")

    st.session_state.dm_mode = st.toggle(
        "🎲 Enable DM Mode",
        value=st.session_state.dm_mode,
        help="Reveals monster stats, weaknesses, and trap DCs. Formats encounters nicely."
    )
    st.session_state.combat_mode_dnd = st.toggle(
        "⚔️ Enable Combat Simulator",
        value=st.session_state.combat_mode_dnd,
        help="Guides you turn-by-turn through D&D combat, rolling for monsters, asking you for rolls, and tracking HP."
    )

    st.markdown("---")
    st.markdown("### Memory Management")
    if st.button("Wipe Conversation Memory", use_container_width=True):
        st.session_state.chat_history_dnd = []
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

# Render History
for i, msg in enumerate(st.session_state.chat_history_dnd):
    with st.chat_message(msg["role"]):
        st.write(msg["content"].replace("$", r"\$"))

# Chat Input execution
question = st.chat_input("Ask about rules, monsters, regions, or backstory generation...")

if question:
    with st.chat_message("user"):
        st.write(question.replace("$", r"\$"))

    with st.chat_message("assistant"):
        with st.spinner("The Oracle is deep within the archives..."):
            try:
                reply, raw_sources, corrected = get_oracle_response(
                    question,
                    st.session_state.chat_history_dnd,
                    known_names,
                    embed_model,
                    st.session_state.dm_mode,
                    st.session_state.combat_mode_dnd
                )
            except Exception as e:
                reply = f"⚠️ The Oracle encountered an error: {e}"
                raw_sources = []
                corrected = question

        if corrected.lower() != question.lower():
            st.caption(f"*(Interpreted search context as: '{corrected}')*")

        st.write(reply.replace("$", r"\$"))

    st.session_state.chat_history_dnd.append({"role": "user", "content": question})
    st.session_state.chat_history_dnd.append({"role": "assistant", "content": reply, "raw_sources": raw_sources})