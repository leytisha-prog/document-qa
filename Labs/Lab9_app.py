import streamlit as st
from openai import OpenAI
import json
import os


# Page config
# -----------------------------
st.set_page_config(
    page_title="Lab 9 - Chatbot with Long-Term Memory",
    page_icon="🤖"
)

st.title("🤖 Chatbot with Long-Term Memory")


# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

MEMORY_FILE = "memories.json"


# Memory helper functions
# -----------------------------
def load_memories():
    """Load memories from JSON file. Return [] if file does not exist."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memories(memories):
    """Save memories list to JSON file."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memories, f, indent=2)

def extract_new_memories(user_msg, assistant_msg, existing_memories):
    """
    Use a small model to extract new user facts worth remembering.
    Returns a list of new facts.
    """
    extraction_system_prompt = """
You extract long-term memories about a user from a conversation.

Only save stable, useful user facts such as:
- name
- school
- major
- preferences
- interests
- hobbies
- location

Do NOT save temporary requests or random one-off details.
Do NOT duplicate existing memories.
Return ONLY valid JSON.
Return a JSON list of strings, like:
["User's name is Alice", "User studies at Syracuse University"]
If there is nothing worth saving, return [].
"""

    extraction_user_prompt = f"""
Existing memories:
{json.dumps(existing_memories)}

User message:
{user_msg}

Assistant response:
{assistant_msg}

Extract any NEW facts about the user worth remembering.
Return ONLY a JSON list.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": extraction_system_prompt},
                {"role": "user", "content": extraction_user_prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        new_memories = json.loads(content)

        if isinstance(new_memories, list):
            # keep only strings and remove duplicates
            cleaned = []
            for m in new_memories:
                if isinstance(m, str) and m not in existing_memories and m not in cleaned:
                    cleaned.append(m)
            return cleaned

    except Exception:
        pass

    return []


# Session state initialization
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# Sidebar memory display
# -----------------------------
st.sidebar.title("Memories")

memories = load_memories()

if memories:
    for m in memories:
        st.sidebar.write(f"- {m}")
else:
    st.sidebar.write("No memories yet. Start chatting!")

if st.sidebar.button("Clear all memories"):
    save_memories([])
    st.rerun()

if st.sidebar.button("Clear chat history"):
    st.session_state.messages = []
    st.rerun()


# Build system prompt with memories
# -----------------------------
system_message = (
    "You are a helpful assistant that remembers information about the user "
    "across conversations. Use saved memories when relevant to personalize responses."
)

if memories:
    memory_str = "\n".join([f"- {m}" for m in memories])
    system_message += (
        "\n\nHere are things you remember about this user from past conversations:\n"
        + memory_str
    )


# Display chat history
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat input
# -----------------------------
if prompt := st.chat_input("Say something about yourself or ask me a question..."):
    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build message list for main assistant call
    conversation = [{"role": "system", "content": system_message}] + st.session_state.messages

    # Main chatbot response
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=conversation,
        temperature=0.7
    )

    assistant_reply = response.choices[0].message.content

    # Save and display assistant response
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)

  
    # Second LLM call: extract memories
    # -----------------------------
    new_memories = extract_new_memories(prompt, assistant_reply, memories)

    if new_memories:
        updated_memories = memories + new_memories
        save_memories(updated_memories)
        st.rerun()



