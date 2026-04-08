import streamlit as st
from openai import OpenAI
import requests 

# Create OpenAI client
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# PART A
if "url_response" not in st.session_state:
    st.session_state.url_response = None 

st.divider()
st.subheader("Image to Poem with OpenAI")
st.write("Enter an image URL and I'll describe the image for you!")
image_url = st.text_input("Image URL", placeholder="Enter an image URL here...")    
if st.button("Write a Poem about this Image"):
    result = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1024,
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a poet who writes vivid and imaginative poems based on images."},
            {"role": "user", "content": "Describe the following image in a poetic way:\n\n" + image_url}    
        ]
    )
    
    
    
    
    
    
    with st.spinner("Calling OpenAI..."):
        try:
            # Call OpenAI API to get a poem description of the image
            response = requests.get(image_url)
            response.raise_for_status() # Check if the request was successful
            data = response.content
            st.session_state.url_response = st.session_state.openai_client.images.describe(data)
            st.success("Image described successfully!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the image: {e}")
        except Exception as e:
            st.error(f"Error describing the image: {e}")
if st.session_state.url_response:
    st.write("Here's the poem description of the image:")
    st.write(st.session_state.url_response)  


    
            
            