# app.py
import streamlit as st
from sentence_transformers import SentenceTransformer
from Scrappers.query_lore import get_oracle_response, get_all_known_names

st.set_page_config(page_title="Warhammer 40k Lore Oracle", page_icon="⚔️", layout="wide")

st.title("⚔️ Warhammer 40k Lore Oracle")
st.caption("Your tactical and narrative companion in the Grim Darkness of the Far Future")


# ── 1. Load Resource Engines ONCE ───────────────────────────────────────────
@st.cache_resource
def load_resources():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    names = get_all_known_names()
    return model, names


embed_model, known_names = load_resources()

# ── 2. Handle State Memory Initializations ─────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "dm_mode" not in st.session_state:
    st.session_state.dm_mode = False
if "combat_mode" not in st.session_state:
    st.session_state.combat_mode = False

# ── 3. Sidebar Actions ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Oracle Settings")
    st.session_state.dm_mode = st.toggle(
        "🎲 Enable Tactician Mode",
        value=st.session_state.dm_mode,
        help="Reveals unit stats, points cost advice, and optimal tactics. Formats comparison tables."
    )
    st.session_state.combat_mode = st.toggle(
        "⚔️ Enable Battle Simulator",
        value=st.session_state.combat_mode,
        help="Guides you turn-by-turn through 40k skirmish battles, rolls dice, and tracks remaining wounds."
    )

    st.markdown("---")
    st.markdown("### Memory Management")
    if st.button("Wipe Command Memory", use_container_width=True):
        st.session_state.chat_history = []
        st.cache_resource.clear()  # Reset caches on wipe
        st.cache_data.clear()
        st.rerun()
    st.caption("Clearing history wipes out the conversation window so you can change topics without context bleed.")

# ── 4. Render Conversation History UI ──────────────────────────────────────
for i, msg in enumerate(st.session_state.chat_history):
    with st.chat_message(msg["role"]):
        # Escape dollar signs to prevent Streamlit from interpreting them as LaTeX math blocks
        st.write(msg["content"].replace("$", r"\$"))
        if "raw_sources" in msg and msg["raw_sources"]:
            with st.expander(f"🔮 View Raw Sources ({len(msg['raw_sources'])})"):
                for src in msg["raw_sources"]:
                    st.markdown(f"**{src['name']}** ({src['content_type']})")
                    st.json(src['extra_data'])

# ── 5. Chat Input Execution Loop ───────────────────────────────────────────
question = st.chat_input("Ask about units, factions, battle rules, or lore history...")

if question:
    with st.chat_message("user"):
        st.write(question.replace("$", r"\$"))

    with st.chat_message("assistant"):
        with st.spinner("The Chronicler is searching the archive vaults..."):
            try:
                reply, raw_sources, corrected = get_oracle_response(
                    question,
                    st.session_state.chat_history,
                    known_names,
                    embed_model,
                    st.session_state.dm_mode,
                    st.session_state.combat_mode
                )
            except Exception as e:
                reply = f"⚠️ The Oracle encountered an error: {e}"
                raw_sources = []
                corrected = question

        if corrected.lower() != question.lower():
            st.caption(f"*(Interpreted search context as: '{corrected}')*")

        # Escape dollar signs to prevent Streamlit from interpreting them as LaTeX math blocks
        st.write(reply.replace("$", r"\$"))
        if raw_sources:
            with st.expander(f"🔮 View Raw Sources ({len(raw_sources)})"):
                for src in raw_sources:
                    st.markdown(f"**{src['name']}** ({src['content_type']})")
                    st.json(src['extra_data'])

    # ── 6. Save back to session history state ───────────────────────────────
    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append({"role": "assistant", "content": reply, "raw_sources": raw_sources})