import streamlit as st
from openai import OpenAI 
from pydantic import BaseModel 

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# Show title and description.
st.title("Lab 6 App - issued by Dre|Eddie|Jake")
user_question = st.text_input(
    "Type your question here..."
)

# ------ Session state (for chaining)
if "last_id" not in st.session_state:
    st.session_state.last_id = None


# ------ Sidebar controls 
st.sidebar.header("Options")
structured = st.sidebar.checkbox("Structured output")
stream_mode = st.sidebar.checkbox("Streaming (basic)", value=False)

st.caption("Web search enabled")

# ------- Structured model
class ResearchSummary(BaseModel):
    main_answer: str
    key_factos: list[str]
    source_hint: str

# ------- User input 
question = st.text_input("Ask a question")

# ------- Function to call API
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
        
        # Safe return
        if response.output_parsed:
            return response.output_parsed
        else:
            return response.output_text
        
    # Normal mode
    else:
            response = client.responses.create(**base)
            st.session_state.last_id = response.id
            return response.output_text

# ------- Display response
if question:
    result = get_response(question)

    # Structured output display
    if structured:
        st.write(result.main_answer)
        st.subheader("Key Facts")
        for fact in result.key_facts:
            st.write(f"- {fact}")
        st.caption(result.source_hint)
   
# --------------- Follow-up (Part B)

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