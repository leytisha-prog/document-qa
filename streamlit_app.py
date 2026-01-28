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
st.sidebar.header(":red[Options]")

summary_type = st.sidebar.radio(
    "Choose summary type:",

    [
        "100-word summary",
        "Two-paragraph summary",
        "Five bullet points"
    ]
)

use_advanced_model = st.sidebar.checkbox("Use advanced model (GPT-4)")

model_name = "gpt-4o" if use_advanced_model else "gpt-4o-mini"




# Create pages for navigation
Lab1_page = st.Page("Labs/Lab1_app.py", title="Lab 1", icon="📄")
Lab2_page = st.Page("Labs/Lab2_app.py", title="Lab 2", icon="🧪")


pg = st.navigation( [Lab1_page, Lab2_page])
st.set_page_config(page_title="My Streamlit App", page_icon=':material/edit:')
pg.run() 