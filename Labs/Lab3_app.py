import streamlit as st
from openai import OpenAI 
import numpy as np


with st.chat_message("user"):
    st.markdown("Hello! How can I assist you today?")
    st.write("Hello icon:wave: how can I assist you today?")
    st.bar_chart(np.random.random(30, 3))

prompt = st.chat_input("Say something")
if prompt:
    st.write(f"user has sent the following prompt: {prompt}")


