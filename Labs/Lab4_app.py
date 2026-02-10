
# SQLite patch for Chroma MUST COME FIRST 
import sys

# A fix
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import chromadb
from pathlib import Path 
from PyPDF2 import PdfReader


# Create ChromaDB client 
chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')

## --------- USING CHROMA DB WITH OPENAI EMBEDDINGS -------- ###

# Create OpenAI client 
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets.OPEN_AI_KEY)

# A function that will add document to collection

# Collection = collection, already established 

# text = extracted text from PDF files

#Embeddings inserted into the collection from OpenAI 
def add_to_collection(collection, text, file_name):

    # Create an embedding 
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )

    # Get the embedding 
    embedding = response.data[0].embedding 

    # Add embedding and document to ChromaDB
    collection.add(
        documents=[text],
        ids=file_name,
        embeddings=[embedding]
    )

#### ----- EXTRACT TEXT FROM PDF ------ ####
# This function extracts text from each syllabus 
# to pass to add_to_collection
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages_text = []

    for page in reader.pahes:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)

    # Join pages and lightly clean 
    text = "\n".join(pages_text).strip()
    return text

#### ----- POPULATE COLLECTION WITH PDFs ------ ####
# This function uses extract_text_from_pdf
# and add_to_collection to put syllabi in ChromDB collection 
def load_pdfs_to_collection(folder_path, collection):

# Check if collection is empty and load PDFs
    if collection.count() == 0:
        loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)

