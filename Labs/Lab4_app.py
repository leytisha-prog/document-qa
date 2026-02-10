
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

##--------- USING CHROMA DB WITH OPENAI EMBEDDINGS --------###

# Create OpenAI client 
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets.OPEN_AI_KEY)

# A function that will add document to collection

# Collection = collection, already established 

# text = extracted text from PDF files
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