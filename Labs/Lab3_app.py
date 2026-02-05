import streamlit as st
from openai import OpenAI 
import numpy as np

st.title ("Chatty G - Lab 3: Streamlit Chat Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from histoty on app rerun 
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])





