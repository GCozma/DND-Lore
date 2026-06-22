import re

def clean_tag(text):
    """
       Converts 5etools {@tag} markup into plain readable text.

       Works in two passes:
         Pass 1 — handle tags we want to reformat (dc, hit, recharge)
         Pass 2 — handle everything else (keep inner text or discard)
       """
    if not text:
        return text
        # ── PASS 1: Tags with special formatting ─────────────────────────────────

        # {@dc 14} → "DC 14"
    text = re.sub(r'\{@dc (\d+)\}', r'DC \1', text)

        # {@hit 9} → "+9"
    text = re.sub(r'\{@hit (\d+)\}', r'+\1', text)

        # {@recharge 5} → "(Recharge 5-6)"
    text = re.sub(r'\{@recharge (\d+)\}', r'(Recharge \1-6)', text)

    # Discard symbol-only tags BEFORE pass 2 can grab their content
    text = re.sub(r'\{@atk[^}]*\}', '', text)  # {@atk mw}, {@atk rw} etc.
    text = re.sub(r'\{@h\}', '', text)  # {@h} — hit marker
    text = re.sub(r'\{@dc (\d+)\}', r'DC \1', text)
    text = re.sub(r'\{@hit (\d+)\}', r'+\1', text)
    text = re.sub(r'\{@recharge (\d+)\}', r'(Recharge \1-6)', text)
    text = re.sub(r'\{@atk[^}]*\}', '', text)
    text = re.sub(r'\{@h\}', '', text)

    # scaledamage: {@scaledamage 8d6|3-9|1d6} → "1d6"
    # Split by | and take the last part
    text = re.sub(
        r'\{@scaledamage ([^}]+)\}',
        lambda m: m.group(1).split("|")[-1],
        text
    )

    # ── PASS 2: Tags where we keep the inner text ─────────────────────────────

        # {@damage 2d6 + 5} → "2d6 + 5"
        # {@dice 1d4}       → "1d4"
        # {@condition frightened} → "frightened"
        # {@spell fireball}       → "fireball"
        # {@creature aboleth}     → "aboleth"
        # {@item longsword}       → "longsword"
        # {@b bold text}          → "bold text"
        # {@i italic text}        → "italic text"
        # Pattern: {@word KEEP THIS PART}
    text = re.sub(r'\{@\w+\s([^}]+)\}', r'\1', text)


        # ── PASS 3: Discard anything remaining ───────────────────────────────────

        # {@atk mw}, {@h}, and any other tags we didn't catch above
        # At this point anything left is a tag with no useful inner text
    text = re.sub(r'\{@[^}]*\}', '', text)

        # Clean up any double spaces left behind after removal
    text = re.sub(r'  +', ' ', text).strip()

    return text

def clean_entries(entries):
    """
       5etools stores trait/action text as a list called "entries".
       Each item in the list can be:
         - A plain string  → clean its tags and return it
         - A dict          → it has nested "entries" inside, go deeper

       This is a RECURSIVE function — it calls itself when it finds
       a nested structure.
       """
    if not entries:
        return ""

    parts=[]

    for entry in entries:
        if isinstance(entry,str):
            parts.append(clean_tag(entry))
        elif isinstance(entry,dict):
    # Complex case — a nested block with its own entries
    # It might have a name (like a sub-heading)
            name=entry.get("name","")
            inner=clean_entries(entry.get('entries',[]))  #calls intself
            if name:
                parts.append(f"{name}:{inner}")
            else:
                parts.append(inner)
    return "\n".join(parts)

# ── TEST ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test = "{@atk mw} {@hit 9} to hit, reach 10 ft. {@h}12 ({@damage 2d6 + 5}) bludgeoning damage. Must make a {@dc 14} Constitution save or become {@condition diseased}."

    print("Before:", test)
    print("After: ", clean_tag(test))
