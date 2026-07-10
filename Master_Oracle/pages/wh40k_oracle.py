# Master_Oracle/pages/wh40k_oracle.py
import sys
import os
import streamlit as st
from sentence_transformers import SentenceTransformer

# 1. Dynamically link the existing Warhammer project modules
WH40K_PROJECT_ROOT = "/home/george/PycharmProjects/Warhammer_oracle"
sys.path.insert(0, WH40K_PROJECT_ROOT)

from Scrappers.query_lore import get_oracle_response, get_all_known_names

# ── Streamlit UI Setup ────────────────────────────────────────────────────────
st.set_page_config(page_title="Warhammer 40k Lore Oracle", page_icon="⚔️", layout="wide")

st.title("⚔️ Warhammer 40k Lore Oracle")
st.caption("Your tactical and narrative companion in the Grim Darkness of the Far Future")


# Load Resources
@st.cache_resource
def load_resources():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    names = get_all_known_names()
    return model, names


embed_model, known_names = load_resources()

# Session State Initializations
if "chat_history_wh" not in st.session_state:
    st.session_state.chat_history_wh = []
if "tactician_mode" not in st.session_state:
    st.session_state.tactician_mode = False
if "combat_mode_wh" not in st.session_state:
    st.session_state.combat_mode_wh = False

# Sidebar Toggles
with st.sidebar:
    st.markdown("### Warhammer Oracle Settings")

    # Visual Engine Status Indicator
    if os.environ.get("GEMINI_API_KEY"):
        st.success("☁️ Engine: Gemini Cloud")
    else:
        st.warning("🖥️ Engine: Local Ollama")

    st.session_state.tactician_mode = st.toggle(
        "🎲 Enable Tactician Mode",
        value=st.session_state.tactician_mode,
        help="Reveals unit stats, points cost advice, and optimal tactics. Formats comparison tables."
    )
    st.session_state.combat_mode_wh = st.toggle(
        "⚔️ Enable Battle Simulator",
        value=st.session_state.combat_mode_wh,
        help="Guides you turn-by-turn through 40k skirmish battles, rolls dice, and tracks remaining wounds."
    )

    st.markdown("---")
    st.markdown("### Memory Management")
    if st.button("Wipe Command Memory", use_container_width=True):
        st.session_state.chat_history_wh = []
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

# Render History
for i, msg in enumerate(st.session_state.chat_history_wh):
    with st.chat_message(msg["role"]):
        st.write(msg["content"].replace("$", r"\$"))

# Chat Input execution
question = st.chat_input("Ask about units, factions, battle rules, or lore history...")

if question:
    with st.chat_message("user"):
        st.write(question.replace("$", r"\$"))

    with st.chat_message("assistant"):
        with st.spinner("The Chronicler is searching the archive vaults..."):
            try:
                reply, raw_sources, corrected = get_oracle_response(
                    question,
                    st.session_state.chat_history_wh,
                    known_names,
                    embed_model,
                    st.session_state.tactician_mode,
                    st.session_state.combat_mode_wh
                )
            except Exception as e:
                reply = f"⚠️ The Oracle encountered an error: {e}"
                raw_sources = []
                corrected = question

        if corrected.lower() != question.lower():
            st.caption(f"*(Interpreted search context as: '{corrected}')*")

        st.write(reply.replace("$", r"\$"))

    st.session_state.chat_history_wh.append({"role": "user", "content": question})
    st.session_state.chat_history_wh.append({"role": "assistant", "content": reply, "raw_sources": raw_sources})