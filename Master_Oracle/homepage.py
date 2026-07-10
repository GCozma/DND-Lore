# homepage.py
import streamlit as st

st.set_page_config(page_title="Lore Oracle Portal", page_icon="🔮", layout="wide")

# Custom Premium Styling for Clickable Cards
st.markdown("""
    <style>
    .portal-container {
        display: flex;
        justify-content: space-around;
        gap: 30px;
        margin-top: 50px;
        flex-wrap: wrap;
    }
    .card-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        width: 45%;
        min-width: 320px;
    }
    .oracle-card {
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        height: 100%;
        cursor: pointer;
    }
    .oracle-card:hover {
        transform: translateY(-5px);
    }
    /* D&D Card Styling */
    .dnd-card {
        border: 2px solid #b8860b; /* Dark Goldenrod */
        box-shadow: 0 0 20px rgba(184, 134, 11, 0.2);
    }
    .dnd-card:hover {
        border-color: #d4af37;
        box-shadow: 0 0 30px rgba(184, 134, 11, 0.5);
    }
    /* WH40K Card Styling */
    .wh40k-card {
        border: 2px solid #00ffff; /* Cyan */
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }
    .wh40k-card:hover {
        border-color: #00ffff;
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
    }
    .card-title {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 15px;
        text-align: center;
    }
    .dnd-title {
        color: #d4af37; /* Metallic Gold */
        text-shadow: 0 0 5px rgba(212, 175, 55, 0.3);
    }
    .wh40k-title {
        color: #00ffff;
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
    }
    .card-description {
        font-size: 16px;
        color: #cccccc;
        margin-bottom: 25px;
        line-height: 1.6;
    }
    .action-prompt {
        text-align: center;
        font-weight: bold;
        margin-top: 20px;
        font-size: 18px;
        transition: color 0.3s ease;
    }
    .dnd-card:hover .action-prompt {
        color: #d4af37;
    }
    .wh40k-card:hover .action-prompt {
        color: #00ffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔮 The Grand Lore Oracle Portal")
st.subheader("Click on either card box below to enter that Oracle.")
st.write("")

# Render the interactive portal layout
st.markdown("""
<div class="portal-container">
    <!-- Clickable D&D Card -->
    <a href="/dnd_oracle" target="_self" class="card-link">
        <div class="oracle-card dnd-card">
            <div class="card-title dnd-title">🐉 D&D 5e Oracle</div>
            <div class="card-description">
                Step into the realms of fantasy. Access the archives of spells, class features, magic items, and deities.
                <br><br>
                • <b>🎲 DM Mode</b>: Reveal trap DCs, monster weaknesses, and stats.<br>
                • <b>⚔️ Combat Simulator</b>: Interactive, turn-by-turn D&D 5e combat assistant.
            </div>
            <div class="action-prompt" style="color: #b8860b;">Enter the Fantasy Archives →</div>
        </div>
    </a>
    <!-- Clickable WH40K Card -->
    <a href="/wh40k_oracle" target="_self" class="card-link">
        <div class="oracle-card wh40k-card">
            <div class="card-title wh40k-title">⚔️ Warhammer 40k Oracle</div>
            <div class="card-description">
                Enter the grim darkness of the far future. Explore faction logs, unit datasheets, and weapon profiles.
                <br><br>
                • <b>🎲 Tactician Mode</b>: Build lists, optimize synergies, and compare stats.<br>
                • <b>⚔️ Battle Simulator</b>: Interactive, turn-by-turn WH40K combat rules simulator.
            </div>
            <div class="action-prompt" style="color: #008b8b;">Enter the Grim Darkness →</div>
        </div>
    </a>
</div>
""", unsafe_allow_html=True)