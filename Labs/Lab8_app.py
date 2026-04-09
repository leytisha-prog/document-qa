import streamlit as st
from openai import OpenAI
import base64

# Create OpenAI client
client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

# Do all Session State Set Up Here
if "url_response" not in st.session_state:
    st.session_state.url_response = None 

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

# PART A - Image URL to Poem

st.divider()
st.header("Lab 8: Image Reader with OpenAI")
st.subheader("Image to Poem with OpenAI")
st.write("Enter an image URL and I'll describe the image for you!")

image_url = st.text_input(
    "Image URL", 
    placeholder="Enter an image URL here..."
    )    

if st.button("Write a Poem about this Image"):
    if image_url.strip():
        try:
            result = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_tokens=1024,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "auto"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Write a poem about this image. "
                                    "Use vivid and descriptive language, and make it at least 4 lines long. "
                                    "Ensure the poem captures the essence and evokes emotions matching the image."
                                )
                            }
                        ]
                    }
                ]
            )
            st.session_state.url_response = result.choices[0].message.content
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter an image URL.")

if st.session_state.url_response:
    st.write(st.session_state.url_response)
    if image_url:
        st.image(image_url)



# PART B - Uploaded image

st.divider()
st.subheader("Image Upload to Poem with OpenAI")

uploaded_file = st.file_uploader(
    "Upload an image and I'll write a poem about it!",
    type=["png", "jpg", "jpeg", "webp", "gif"]
)

if st.button("Write a Poem about this Uploaded Image"):
    if uploaded_file is not None:
        try:
            image_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # figure out mime type from uploaded file
            mime_type = uploaded_file.type
            if not mime_type:
                mime_type = "image/jpeg"

            result = client.chat.completions.create(
                model="gpt-4.1-mini",
                max_tokens=1024,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}",
                                    "detail": "auto"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Write a poem about this image. "
                                    "Use vivid and descriptive language, and make it at least 4 lines long. "
                                    "Ensure the poem captures the essence and evokes emotions matching the image."
                                )
                            }
                        ]
                    }
                ]
            )

            st.session_state.upload_response = result.choices[0].message.content

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload an image first.")

if st.session_state.upload_response:
    st.write(st.session_state.upload_response)

if uploaded_file is not None:
    st.image(uploaded_file)
    
