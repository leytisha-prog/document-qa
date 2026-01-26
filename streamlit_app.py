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

# Create pages for navigation
create_page = st.Page('create.py', title='Create entry', icon=':material/add_circle')
delete_page = st.Page('delete.py', title='Delete entry', icon=':material/delete')

pg = st.navigation( [create_page, delete_page],)
st.set_page_config(page_title="My Streamlit App", page_icon=':material/edit:')
pg.run() 