import streamlit as st
from openai import OpenAI

# Default parameters
st.set_page_config(page_title="OpenAI Streamlit App", page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

    # Configure global settings for the Streamlit app (must be called from the top)
st.set_page_config(
        page_title="Leytisha's App",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://www.example.com/help',
            'Report a bug': 'https://www.example.com/bug',
            'About': "This is a simple Streamlit app using OpenAI's API."
        }
    )