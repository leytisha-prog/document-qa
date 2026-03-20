import streamlit as st

# ---------------------------------------------------
# MUST be the FIRST Streamlit command in the file
# ---------------------------------------------------
st.set_page_config(
    page_title="Leytisha's App",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# Create pages
# ---------------------------------------------------
Lab1_page = st.Page("Labs/Lab1_app.py", title="Lab 1", icon="📄")
Lab2_page = st.Page("Labs/Lab2_app.py", title="Lab 2", icon="🧪")
Lab3_page = st.Page("Labs/Lab3_app.py", title="Lab 3", icon="🔬")
Lab4_page = st.Page("Labs/Lab4_app.py", title="Lab 4", icon="🤖")
Lab5_page = st.Page("Labs/Lab5_app.py", title="Lab 5", icon="☀️"bs_page]))

# ✅ Make Lab 5 the default
Lab6_page = st.Page(
    "Labs/Lab6_app.py",
    title="Lab 6",
    icon="⋆ 🗞️ ₊˚⊹ ♡",
    default=True
)

# ---------------------------------------------------
# Navigation
# ---------------------------------------------------
pg = st.navigation([Lab1_page, Lab2_page, Lab3_page, Lab4_page, Lab5_page])
pg.run()    