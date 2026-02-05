import streamlit as st
from openai import OpenAI 
import numpy as np

st.title ("Chatty G - Lab 3: Streamlit Chat Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun 
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Hey ya'll! What's up?"):
    # Display user message in chat message container
    with st.chat_message("user") :
        st.markdown (prompt)
        # Add user message to chat history 
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = f"Echo: {prompt}"
        # Display assistant response in chat message container 
        with st.chat_message("assistant"):
            st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    





