
# 1. SQLite patch for Chroma MUST BE FIRST ----------------------
import sys

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# 2. Imports ---------------------------------------------------
import streamlit as st
from openai import OpenAI
import chromadb
from pathlib import Path 
from PyPDF2 import PdfReader


# APP UI -----------------------------
###----Main App----###
st.title('Lab 4: Chatbot Using RAG')
### ----------------------------------


# 3. Create ChromaDB and client setup --------------------------
chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')

# Create OpenAI client 
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])



###--------- HELPERS --------- ###
# 4. Function definitions (NO Streamlit UI here) -----------------
#Embeddings inserted into the collection from OpenAI 

def safe_id_from_filename(pdf_file: Path) -> str:
            return pdf_file.stem.replace(" ", "_")


def add_to_collection(collection, text, str, doc_id: str):
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
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[{"souce": f"{doc_id}.pdf"}]
    )


#### ----- EXTRACT TEXT FROM PDF ------ ####
# This function extracts text from each syllabus 
# to pass to add_to_collection

def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages_text = []

    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)

    # Join pages and lightly clean 
    return "\n".join(pages_text).strip()
     


#### ----- POPULATE COLLECTION WITH PDFs ------ ####
# This function uses extract_text_from_pdf
# and add_to_collection to put syllabi in ChromDB collection 

folder_path = "./Labs/pdf_files"

def load_pdfs_to_collection(folder_path: str, collection) -> int:
    folder = Path(folder_path)
    pdf_files = sorted(folder.glob("*.pdf"))

    added_count = 0

    for pdf_file in pdf_files:
        text = extract_text_from_pdf(str(pdf_file))

        # Skip empty PDFs
        if not text:
            continue
        
        # Define doc id
        doc_id = safe_id_from_filename(pdf_file)

        # Skip if already exists
        # Chroma will error if you add the same id again
        try:
            add_to_collection(collection, text, doc_id)
            added_count += 1
        except Exception as e:
            # If it's already there or another add error, you can skip/log
            # You can also st.write(...) if you want to see it in the UI
            continue
        return added_count



# 5 EXECUTION LOGIC HERE - Check if collection is empty and load PDFs ------------

PDF_FOLDER = "./Labs/Lab-04-Data"

with st.spinner("Checking/creating Chroma index..."):
    if collection.count() == 0:
        loaded = load_pdfs_to_collection('./Lab-04-Data/', collection)
        st.success(f"Loaded {loaded} PDFs into Chroma.")
    else:
        st.info("Chroma collection already populated.")



# 6 UI/QUERY LOGIC ----------------------------------------------------------------
st.header("Ask a question about the syllabi")

### --------- QUERYYING A COLLECTION - ONLY USED FOR TESTING --------- ###
topic = st.sidebar.text_input('Topic', placeholder='Type your topic (e.g., GenAI)...')

if topic:
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=topic,
        model='text-embedding-3-small')
    
    # Get the embedding
    query_embedding = response.data[0].embedding

    # Get the text related to this question (this prompt)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3, # The number of closest documents to return
        include=["documents", "metadatas", "ids"]
    )
    
    # Display the results
    st.subheader(f'Results for: {topic}')

    for i in range(len(results['documents'][0])):
        doc_id = results['ids'][0][i]
        source = results["metadatas"][0][i].get("source", "unknown")

        st.write(f'**{i+1}. {doc_id}**')

        with st.expander(f"Show text for {doc_id}"):
            st.write(results["documents"][0][i])

else:
    st.info('Enter a topic in the sidebar to search the collection')

