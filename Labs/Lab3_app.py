import streamlit as st
from openai import OpenAI 

with st.chat_message("user"):
    st.markdown("Hello! How can I assist you today?")
    st.write("Hello icon=:wave: how can I assist you today?")
    