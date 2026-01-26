import streamlit as st
from openai import OpenAI


st.Page(
    # String path to the page's Python file, relative to the main app file
    "Labs/Lab2_app.py",

    # Optional title for the page. If None, Streamit infers the title
    title="Lab 2: OpenAI Integration",

    # Optional icon for the page. Can be a string (e.g., emoji) or an image URL
    icon="None",    

    # Optional URL path for the page (what shows in the address bar).
    # If None, Streamlit infers the path from the file name
    url_path="None",

    # Whether this page is the default page loaded on app start
    # Only one page should be set to True
    default=True,

)
