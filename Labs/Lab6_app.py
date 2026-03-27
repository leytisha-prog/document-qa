import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

# ----------------------------
# Setup
# ----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.title("Lab 6: Multi-Turn Agent")

# ----------------------------
# Session state (for chaining)
# ----------------------------
if "last_id" not in st.session_state:
    st.session_state.last_id = None

# ----------------------------
# Sidebar options
# ----------------------------
structured = st.sidebar.checkbox("Structured output")
streaming = st.sidebar.checkbox("Streaming (basic)", value=False)

st.caption("Web search enabled")

# ----------------------------
# Structured model
# ----------------------------
class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str

# ----------------------------
# User input
# ----------------------------
question = st.text_input("Ask a question")

# ----------------------------
# Function to call API
# ----------------------------
def get_response(user_input):
    base = {
        "model": "gpt-4o",
        "instructions": "You are a helpful research assistant. Cite sources.",
        "input": user_input,
        "tools": [{"type": "web_search_preview"}],
    }

    # Add chaining if exists
    if st.session_state.last_id:
        base["previous_response_id"] = st.session_state.last_id

    # Structured mode
    if structured:
        response = client.responses.parse(
            **base,
            text_format=ResearchSummary
        )
        st.session_state.last_id = response.id
        return response.output_parsed

    # Normal mode
    else:
        response = client.responses.create(**base)
        st.session_state.last_id = response.id
        return response.output_text

# ----------------------------
# Display response
# ----------------------------
if question:
    result = get_response(question)

    # Structured output display
    if structured:
        st.write(result.main_answer)
        st.subheader("Key Facts")
        for fact in result.key_facts:
            st.write(f"- {fact}")
        st.caption(result.source_hint)

    # Normal output
    else:
        st.write(result)

# ----------------------------
# Follow-up (Part B)
# ----------------------------
if st.session_state.last_id:
    followup = st.text_input("Ask a follow-up question")

    if followup:
        result = get_response(followup)

        if structured:
            st.write(result.main_answer)
            st.subheader("Key Facts")
            for fact in result.key_facts:
                st.write(f"- {fact}")
            st.caption(result.source_hint)
        else:
            st.write(result)