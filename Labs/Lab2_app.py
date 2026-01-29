import streamlit as st
from openai import OpenAI 
import PyPDF2
import io

def read_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # api_key = st.text_input("OpenAI API Key", type="password")
      
    try:
        # Validation line (right here)
        OpenAI(api_key=openai_api_key).chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )

        st.success("API key validated ✅")

        # Existing code continues unchanged
        client = OpenAI(api_key=openai_api_key)

        uploaded_file = st.file_uploader(
            "Upload a document (.txt or .md)", type=("txt", "md")
        )

    except Exception:
        st.error("Invalid API key. Please try again.", icon="❌")


# Show title and description.
st.title("Document Summarizer App")
st.write(
    "Upload a PDF or a TXT document below and ask a question about it – GPT will answer! "
)

st.sidebar.header("Summary Options")

summary_type = st.sidebar.radio(
    "Choose summary type:",
    [
        "100-word summary",
        "Two-paragraph summary",
        "Five bullet points",
    ],
)

use_advanced_model = st.sidebar.checkbox("Use advanced model (gpt-4o)")

model_name = "gpt-4o" if use_advanced_model else "gpt-4o-mini"

uploaded_file = st.file_upload(
    "Upload a document (.txt or .pdf)", type=("txt", "pdf")
)

if summary_type == "100-word summary":
    summary_instruction = "Summarize the following document in approximately 100 words."
elif summary_type == "Two-paragraph summary":
    summary_instruction = "Summarize the following document in two concise paragraphs."
else:
    summary_instruction = "Summarize the following document in five bullet points."

if uploaded_file:
    document_text = read_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else uploaded_file.read().decode()

    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes documents based on user instructions.",
                    },
                    {
                        "role": "user",
                        "content": f"{summary_instruction}\n\nDocument:\n{document_text}",
                    }
                ]
            )
        st.subheader("Summary:")
        st.write(response.choices[0].message.content)
        st.write("Summary generated successfully!")




