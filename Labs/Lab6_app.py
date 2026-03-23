import streamlit as st
from openai import OpenAI 
import pydantic

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# Show title and description.
st.title("Lab 6 App - issued by Dre|Eddie|Jake")
user_question = st.text_input(
    "Type your question here..."
)

if user_question:
    response = client.responses.create(
        model="gpt-5",
        instructions="You are a helpful assistant. Answer in a single paragraph,",
        input=user_question
    )
    st.write(response.output_text)
    
    