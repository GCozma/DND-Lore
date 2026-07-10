# warhammer_oracle/Scrappers/query_lore.py
import sqlite3
import os
import json
import chromadb
import ollama
import difflib
import re
from sentence_transformers import SentenceTransformer

# Optional imports for Gemini Cloud fallback
try:
    from google import genai
    from google.genai import types

    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False

from Scrappers.constants import DB_PATH, CHROMA_PATH

MODEL_NAME = "llama3.1"

UNIFIED_SYSTEM_PROMPT = """You are the Warhammer 40k Lore Oracle, a grand chronicler of the Imperium and tactical adviser.
You answer questions using the campaign database material provided.

STRICT RULES:
1. If the database material contains the answer, use it accurately, explain it in detail, and cite the entries you drew from.
2. If the database material is partially relevant or missing, say: "The archives do not cover [X] specifically." Then you MUST offer general Warhammer 40k universe lore to answer the question in full detail. Label this general lore: "⚠️ Archives of the Imperium (General Lore):"
3. Use a detailed, formal, dark, and atmospheric gothic tone fitting for the grim darkness of the Warhammer 40k universe (no casual or modern robotic descriptions).
4. Break down complex explanations using Markdown headers, lists, and quote blocks. Always compare stats and units using Markdown tables.
5. NEVER invent campaign-specific names, locations, squads, or events.
6. When using the execute_sql tool, analyze the returned data carefully to answer the user's question.
7. If you need to search or filter database entries (e.g. finding units by faction, toughness, or weapons), call the execute_sql tool natively. Do NOT write out the JSON of the function call in your text reply; instead, call the tool directly.
8. NEVER use robotic meta-language talking about the database, query outputs, errors, columns, or tools (e.g., do NOT say things like 'Based on the output of the execute_sql tool...', 'According to the reference material...', 'Looking at the SQL query result...', 'Since there is no column...'). Simply integrate the retrieved information naturally and write your response directly as if you natively know it.
9. NEVER mention database errors, query errors, missing columns, or database structure to the user. If a tool fails or cannot find a column, resolve it silently and behave as if the files do not cover the detail, without letting the user know there was a technical database error.
10. MATHEMATICAL ACCURACY: You must double-check all arithmetic. When a unit takes damage, you MUST show the math subtraction in brackets (e.g. 'takes 6 damage [8 Wounds - 6 = 2 Wounds remaining]'). If a unit's Wounds reach 0, it immediately dies/is destroyed and cannot take any actions in the remainder of the simulation."""


def get_all_known_names():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM content")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def fix_typos_in_query(query_text, known_names):
    CORE_TERMS = ["faction", "unit", "weapon", "wargear", "stratagem", "rule",
                  "marine", "necron", "warrior", "dreadnought", "intercessor",
                  "overlord", "lychguard", "terminator"]

    # Common terms that should never be auto-corrected
    EXCLUDE_CORRECTION = {"fight", "shoot", "charge", "roll", "help", "turn",
                          "phase", "hit", "wound", "save", "armour", "toughness"}

    words = query_text.split()
    corrected_words = []

    known_set_lower = {name.lower() for name in known_names}

    for word in words:
        clean_word = "".join(c for c in word if c.isalnum()).lower()

        if not clean_word or len(clean_word) <= 2:
            corrected_words.append(word)
            continue

        if clean_word in EXCLUDE_CORRECTION:
            corrected_words.append(word)
            continue

        if clean_word in CORE_TERMS or clean_word in known_set_lower:
            corrected_words.append(word)
            continue

        # Correct typos of core terms
        core_matches = difflib.get_close_matches(clean_word, CORE_TERMS, n=1, cutoff=0.8)
        if core_matches:
            corrected_words.append(core_matches[0])
            continue

        # Correct typos of specific unit names in database
        if len(clean_word) >= 4:
            db_matches = difflib.get_close_matches(clean_word, known_names, n=1, cutoff=0.8)
            if db_matches:
                corrected_words.append(db_matches[0])
                continue

        corrected_words.append(word)

    return " ".join(corrected_words)


def get_full_entry(cursor, row_id):
    cursor.execute("SELECT * FROM content WHERE id = ?", (row_id,))
    return cursor.fetchone()


def get_exact_name_entry(cursor, name):
    cursor.execute("SELECT * FROM content WHERE name = ? COLLATE NOCASE", (name,))
    return cursor.fetchone()


_chroma_client = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def search(query_text, n_results=15, model=None, known_names=None):
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    entries = []
    seen_names = set()

    if known_names:
        query_lower = f" {query_text.lower()} "
        for name in known_names:
            if f" {name.lower()} " in query_lower:
                row = get_exact_name_entry(cursor, name)
                if row:
                    row_id, r_name, universe, source, content_type, description, extra_data = row
                    if r_name not in seen_names:
                        entries.append({
                            "name": r_name,
                            "content_type": content_type,
                            "description": description,
                            "extra_data": json.loads(extra_data) if extra_data else {}
                        })
                        seen_names.add(r_name)

    client = _get_chroma_client()
    try:
        collection = client.get_collection(name="lore")
        query_embedding = model.encode([query_text]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_results, collection.count()),
            include=["distances"]
        )
        matched_ids = results["ids"][0]
        for row_id in matched_ids:
            row = get_full_entry(cursor, int(row_id))
            if row:
                _, name, universe, source, content_type, description, extra_data = row
                if name not in seen_names:
                    entries.append({
                        "name": name,
                        "content_type": content_type,
                        "description": description,
                        "extra_data": json.loads(extra_data) if extra_data else {}
                    })
                    seen_names.add(name)
    except Exception:
        pass

    conn.close()
    return entries


def format_context(entries, max_chars=4000):
    blocks = []
    for entry in entries:
        description = entry["description"] if entry["description"] else ""
        if len(description) > max_chars:
            description = description[:max_chars] + "... [truncated]"

        block = f"## {entry['name']} ({entry['content_type']})\n"
        block += f"{description}\n"
        if entry["extra_data"]:
            extra_str = json.dumps(entry['extra_data'])
            if len(extra_str) > max_chars:
                extra_str = extra_str[:max_chars] + "... [truncated]"
            block += f"Details: {extra_str}\n"
        blocks.append(block)

    return "\n---\n".join(blocks)


def execute_sql(query):
    """Executes a SQL query against the lore database and returns results."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()

        if not rows:
            return "Query executed successfully. 0 results found."

        result = [dict(zip(columns, row)) for row in rows]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"SQL Error: {str(e)}"


def extract_json_query(text):
    """Fallback parser to extract SQL query if the local LLM outputs JSON as text instead of a native tool call."""
    if not text:
        return None

    # Find markdown JSON blocks
    blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if not blocks:
        blocks = re.findall(r'```\s*(.*?)\s*```', text, re.DOTALL)

    candidates = blocks if blocks else [text]
    for content in candidates:
        try:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end + 1]
                obj = json.loads(json_str)
                if isinstance(obj, dict):
                    query = obj.get("query")
                    if not query and "parameters" in obj:
                        query = obj["parameters"].get("query")
                    if query:
                        return query
        except Exception:
            continue
    return None


# The tool definition for Ollama
sql_tool_ollama = {
    "type": "function",
    "function": {
        "name": "execute_sql",
        "description": "Execute a raw SQL query on the 'content' table to find specific Warhammer 40k datasheets. Columns: id, name, universe, source, content_type, description, extra_data. All custom stats (e.g. faction, m, t, sv, w, ld, oc, invulnerable, weapons) are stored inside the 'extra_data' column as a JSON object. You MUST use json_extract(extra_data, '$.field_name') to query them. Example: SELECT name, json_extract(extra_data, '$.weapons') FROM content WHERE content_type='unit' AND name='Terminator Squad'; never query weapons or stats as top-level columns.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The exact SQL query to execute."
                }
            },
            "required": ["query"]
        }
    }
}


def get_oracle_response(question, chat_history, known_names, embed_model, dm_mode=False, combat_mode=False):
    corrected_question = fix_typos_in_query(question, known_names)

    if combat_mode:
        mode_prompt = (
            "CURRENT MODE: BATTLE SIMULATOR. You run turn-by-turn interactive Warhammer 40k skirmish battles.\n\n"
            "Maintain a running state of the battle in your mind, including: Turn Number, Active Factions, Unit Wounds (HP), and weapons.\n"
            "STRICT BATTLE INTERACTION RULES:\n"
            "1. If battle is starting (no unit wounds or initiative exists in history), ask the user for their squad name, total squad wounds (HP), and faction (e.g. Space Marines). Describe the battlefield setup, the enemy squad, and their weapon stats. Do NOT make any rolls or start the first turn yet. Ask: 'Would you like me to roll to see who goes first, or do you want to roll it yourself?' then STOP writing immediately and wait for their reply.\n"
            "2. Once the battle starts, run it turn-by-turn. NEVER run through multiple rounds or turns in a single message. Do NOT repeat the initial setup or unit descriptions.\n"
            "3. On the Player's turn: describe the tactical situation, state what weapons they can fire or if they can charge. Then, ALWAYS ask the player: 'Would you like me to roll the hit and wound rolls for you, or do you want to roll them yourself?' and STOP writing immediately. Do NOT simulate the rolls, and do NOT write any further text.\n"
            "4. If the player responds and asks you to roll (e.g. 'roll for me', 'yes', 'shoot them'), simulate the rolls yourself using 40K 10th edition logic (Roll to Hit using BS/WS, Roll to Wound comparing S vs T, target rolls Armour Saves modified by AP). Describe the exact rolls (e.g. '2 hits on 3+, 1 wound on 4+, Necron Warrior rolls a 2 and fails save'), calculate wounds lost, and proceed to the next combatant's turn.\n"
            "5. If the player rolls themselves and provides results (e.g., '2 wounds got through'), apply the results directly to the enemy's wounds and proceed to the next turn.\n"
            "6. On the Enemy's turn: describe the enemy's move, simulate the enemy's attack rolls, state what saves the player must roll (e.g. 'Roll a 3+ save'), and pause to ask: 'Would you like me to roll your saves, or do you want to roll?' then STOP writing.\n"
            "7. Do NOT output robotic meta-phrases explaining tool outputs or SQL/database column details. If a query fails or columns are missing, handle it silently without letting the user know there was a database issue.\n"
            "8. Do NOT print duplicate lists of the combatants in your message body. Only output the final battle status block.\n"
            "9. ALWAYS print a clean '⚔️ BATTLE STATUS' block at the very bottom of your response. Use exactly the markdown structure below (ensure a double newline precedes it, and put each item on its own separate line to prevent horizontal merging):\n\n"
            "⚔️ BATTLE STATUS\n\n"
            "Turn: [Number]\n\n"
            "Factions in Combat:\n"
            "- [Your Unit] ([Faction])\n"
            "  Wounds: [Number]/[Max]\n"
            "- [Enemy Unit] ([Faction])\n"
            "  Wounds: [Number]/[Max]\n"
        )
    elif dm_mode:
        mode_prompt = "CURRENT MODE: TACTICIAN MODE. You act as a list-building and tactics adviser. Reveal hidden unit stats, point values, synergies, and wargear combos. Output tactical tables comparing weapons or squad options, and suggest optimal strategies."
    else:
        mode_prompt = "CURRENT MODE: LORE MODE. You act as a Warhammer 40k Chronicler. STRICTLY DO NOT reveal tabletop points, dice values, or game stats. Explain the narrative lore, faction history, legendary heroes, and universe details in a rich, dark, atmospheric tone."

    system_prompt = f"{UNIFIED_SYSTEM_PROMPT}\n\n{mode_prompt}"

    follow_up_indicators = ["it", "they", "he", "she", "them", "those"]
    question_words = corrected_question.lower().split()
    pronoun_count = sum(1 for word in question_words if word in follow_up_indicators)
    is_short = len(question_words) <= 5
    contains_proper_noun = any(word.capitalize() in known_names for word in corrected_question.split())

    is_follow_up = (len(chat_history) > 1
                    and pronoun_count >= 1
                    and is_short
                    and not contains_proper_noun)

    entries = []
    if is_follow_up:
        user_prompt = corrected_question
    else:
        entries = search(corrected_question, n_results=15, model=embed_model, known_names=known_names)
        context = format_context(entries)
        user_prompt = (
            "=== VERIFIED CAMPAIGN FILE DATA ===\n"
            f"{context}\n"
            "=== END OF FILE DATA ===\n\n"
            f"USER QUESTION: {corrected_question}\n\n"
            "Answer using the campaign files above or the execute_sql tool."
        )

    # ── Check for Gemini Cloud API Key ─────────────────────────────────────────
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if HAS_GEMINI_SDK and gemini_api_key:
        # ── CLOUD ENGINE: Gemini 1.5 Flash ────────────────────────────────────
        try:
            client = genai.Client(api_key=gemini_api_key)

            # Map history to Gemini format
            api_history = []
            for msg in chat_history[-8:]:
                role = "model" if msg["role"] == "assistant" else "user"
                api_history.append({"role": role, "parts": [{"text": msg["content"]}]})

            contents = api_history + [{"role": "user", "parts": [{"text": user_prompt}]}]

            # Define tool function wrapper
            def sql_tool_wrapper(query: str) -> str:
                return execute_sql(query)

            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[sql_tool_wrapper],
                    temperature=0.4
                )
            )

            reply = response.text

            if response.function_calls:
                for call in response.function_calls:
                    if call.name == "sql_tool_wrapper":
                        query = call.args.get("query")
                        sql_result = execute_sql(query)

                        follow_up_contents = contents + [
                            {"role": "model", "parts": [{"text": reply if reply else "Executing query..."}]},
                            types.Part.from_function_response(
                                name="sql_tool_wrapper",
                                response={"result": sql_result}
                            )
                        ]

                        final_response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=follow_up_contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                tools=[sql_tool_wrapper],
                                temperature=0.4
                            )
                        )
                        reply = final_response.text

            if reply:
                return reply, entries, corrected_question

        except Exception as cloud_err:
            print(f"Cloud Engine failed ({cloud_err}). Falling back to local Ollama...")

    # ── LOCAL ENGINE: Ollama Llama 3.1 ─────────────────────────────────────────
    api_history = []
    for msg in chat_history[-8:]:
        api_history.append({"role": msg["role"], "content": msg["content"]})

    api_payload = [{"role": "system", "content": system_prompt}] + api_history + [
        {"role": "user", "content": user_prompt}]

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=api_payload,
            options={"num_ctx": 16384, "temperature": 0.4},
            tools=[sql_tool_ollama]
        )

        reply = response.get("message", {}).get("content", "")
        tool_query = None
        tool_call_id = None

        if response.get("message", {}).get("tool_calls"):
            api_payload.append(response["message"])
            for tool_call in response["message"]["tool_calls"]:
                if tool_call["function"]["name"] == "execute_sql":
                    tool_query = tool_call["function"]["arguments"].get("query", "")
                    tool_call_id = tool_call.get("id")

        if not tool_query and reply:
            tool_query = extract_json_query(reply)
            if tool_query:
                tool_call_id = "call_fallback"
                api_payload.append({
                    "role": "assistant",
                    "content": reply,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": "execute_sql",
                            "arguments": {"query": tool_query}
                        }
                    }]
                })

        if tool_query:
            sql_result = execute_sql(tool_query)
            tool_msg = {
                "role": "tool",
                "name": "execute_sql",
                "content": sql_result
            }
            if tool_call_id:
                tool_msg["tool_call_id"] = tool_call_id

            api_payload.append(tool_msg)

            final_response = ollama.chat(
                model=MODEL_NAME,
                messages=api_payload,
                options={"num_ctx": 16384, "temperature": 0.4},
                tools=[sql_tool_ollama]
            )
            reply = final_response["message"]["content"]
        else:
            reply = response["message"]["content"]

    except Exception as e:
        return f"⚠️ Oracle connection error: {e}", [], corrected_question

    return reply, entries, corrected_question