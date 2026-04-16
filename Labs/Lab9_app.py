import streamlit as st
from openai import OpenAI
import json
import os


# Create OpenAI client
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# ---- Configuration
st.set_page_config(page_title="Lab 9 - Chatbot with Long-Term Memory", page_icon="🤖")

# ---- Set Memory 
def load_memories ():
    if os.path.exists("memories.json"):
        with open("memories.json", "r") as f:
            return json.load(f)
        return []

memories = load_memories()

system_message = "You are a helpful assistant that can remember information about the user across conversations. You can store and retrieve memories to provide personalized responses."
if memories:
    memory_str = "\n".join([f"- {m}" for m in memories])
    system_message += (
            "\n\nHere are things you remember about this user"
            "from previous conversations:\n" + memory_str +
            "\nUse this information to personalize your responses."
        )

messages = [{"role": "system", "content": system_message}]
messages += st.session_state.messages

# ----- Second LLM Call with Memory 
user_msg = st.session_state.messages[-2]["content"]
assistant_msg = st.session_state.messages[-1]["content"]

extraction_prompt = f"""Analyze this conversation and extract new facts 
about the user worth remembering for future interactions.

Already known memories:
{json.dumps(memories)}

User message: {user_msg}
Assistant response: {assistant_msg}

Return ONLY a JSON list of new facts about the user that are not already in the known memories [].
Example: ["User's name is Alice", "User studies at Syracuse University"]"""

response = client.chat.completions.create(
    model="gpt-4.1-nano",
    messages=[{"role": "system", "content": extraction_prompt}]
)

def save_memories(memories):
    with open("memories.json", "w") as f:
        json.dump(memories, f)

# ---- Streamlit UI 
st.sidebar.title("Memories")
memories = load_memories()
if memories:
    for m in memories:
        st.sidebar.write(f"- {m}")
else:
    st.sidebar.write("No memories yet. Start chatting to create memories!")

if st.sidebar.button("Clear all memories"):
    save_memories([])
    st.rerun()



