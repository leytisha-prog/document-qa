import streamlit as st
from openai import OpenAI
import requests 
import base64

# Create OpenAI client
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# PART A
if "url_response" not in st.session_state:
    st.session_state.url_response = None 

st.divider()
st.header("Lab 8: Image Reader with OpenAI")
st.subheader("Image to Poem with OpenAI")
st.write("Enter an image URL and I'll describe the image for you!")
image_url = st.text_input("Image URL", placeholder="Enter an image URL here...")    
if st.button("Write a Poem about this Image"):
    result = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1024,
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url, "detail": "auto"}},
                {"type": "text", "text": "Write a poem about this image. Write using vivid and descriptive language, and make it at least 4 lines long."
                 "Ensure the poem captures the essence and evokes emotions matching the image, bringing the image to life."}
            ]   
        }]
    )      
if st.session_state.url_response:
    st.write(st.session_state.url_response) 
    st.image(image_url)

# PART B
session_state = st.session_state
if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

st.divider()
st.subheader("Image Upload to Poem with OpenAI")
uploaded_file = st.file_uploader(type=["png", "jpg", "jpeg", "webp", "gif"] )      

st.button("Write a Poem about this Uploaded Image")
if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    result = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1024,
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_base64", "image_base64": {"base64": image_base64, "detail": "auto"}},
                {"type": "text", "text": "Write a poem about this image. Write using vivid and descriptive language, and make it at least 4 lines long."
                 "Ensure the poem captures the essence and evokes emotions matching the image, bringing the image to life."}
            ]   
        }]
    )      
if st.session_state.upload_response:
    st.write(st.session_state.upload_response) 
    st.image(uploaded_file)

    
    
    
    
    
    
   


    
            
            