
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


# This file lives in Labs/, build paths from repos root
BASE_DIR = Path(__file__).resolve().parents[1]
PDF_FOLDER = BASE_DIR / "Labs" / "Lab-04-Data"    # Put 7 PDFs here

st.write("PDF folder:", str(PDF_FOLDER))
st.write("PDFs found:", [p.name for p in PDF_FOLDER.glob("*.pdf")])


CHROMA_DIR = BASE_DIR / "ChromaDB_for_Lab"


# APP UI -----------------------------
###----Main App----###
st.title('Lab 4: Chatbot Using RAG')
### ----------------------------------


# 3. Create ChromaDB and client setup --------------------------
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection("Lab4Collection")
st.write("Docs in collection:", collection.count())

# Create OpenAI client 
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])



###--------- HELPER FUNCTIONS --------- ###

# 4. Function definitions (NO Streamlit UI here) -----------------
#Embeddings inserted into the collection from OpenAI 

def safe_id_from_filename(pdf_file: Path) -> str:
    return pdf_file.stem.replace(" ", "_")


def add_to_collection(collection, text: str, doc_id: str, source_name: str):
    # Create an embedding 
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    # Get the embedding 
    embedding = response.data[0].embedding 

    # Add embedding and document to ChromaDB
    collection.add(
        documents=[text],
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[{"source": source_name}]
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


def load_pdfs_to_collection(folder_path: Path, collection) -> int:
    pdf_files = sorted(folder_path.glob("*.pdf"))
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
            add_to_collection(collection, text, doc_id, pdf_file.name)
            added_count += 1
        except Exception:
            # If it's already there or another add error, you can skip/log
            # You can also st.write(...) if you want to see it in the UI
            continue
        
    return added_count #put it outside the loop (Thanks TA!) 


# 5 EXECUTION LOGIC HERE - Check if collection is empty and load PDFs ------------

# Create the ChromaDB once and store in session (save money on rebuilding embeddings each rerun)
def build_lab4_vectordb():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("Lab4Collection")

    if collection.count()== 0:
        loaded = load_pdfs_to_collection(PDF_FOLDER, collection)
        st.success(f"Loaded {loaded} PDFs into Chromaa.")
    return collection

def retrieve_context(question: str, collection, k: int = 3):
    client = st.session_state.openai_client
    q_emb = client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"]
    )

    docs = (results.get("documents") or [[]]) [0]
    metas = (results.get("metadatas") or [[]]) [0]
    ids = (results.get("ids") or [[]]) [0]

    blocks = []
    sources = []

    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        doc_id = ids[i] if i < len(ids) else meta.get("source", f"doc_{i+1}")
        src = meta.get("source", doc_id)

        sources.append(src)
        blocks.append(f"[SOURCE: {src}]\n{doc}")

    return "\n\n---\n\n".join(blocks), sources

def answer_with_hybrid_rag(question: str, context: str):
    """
    Hybrid RAG:
    - Use retrived PDFs if relevant.
    - If not found in PDFs, still answer using general knowledge,
      but clearly state it is not from the course documents.
    """ 
    client = st.session_state.openai_client
    
    # Prevents huge prompts, since PDFs are stored as full text
    MAX_CHARS = 12000
    context = (context or "") [:MAX_CHARS]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a course information chatbot."
                "You have access to retrieved course documents via RAG."
                "If the answer is found in the course documents, use them and say you used course documents via RAG."
                "If the answer is NOT found in the course documents, you may answer using general knowledge,"
                "but clearly state that the information is not from the course documents."

            )
        },
        {
            "role": "user",
            "content": f"""
QUESTION:
{question}

RETRIEVED COURSE DOCUMENT EXCERPTS:
{context}

First decide whether the excerpts contain relevant information.
Then answer accordingly,
""".strip()
        }
    ]
    
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3
    )
    return resp.choices[0].message.content

# 6. BUILD/REUSE VECTOR DB ---------------------------------------------------------
if "Lab4_VectorDB" not in st.session_state:
    with st.spinner("Building Lab4 vector DB (first run only)..."):
        st.session_state.Lab4_VectorDB = build_lab4_vectordb()

collection = st.session_state.Lab4_VectorDB
st.write("Docs in collection:", collection.count())


# 7. SIDEBAR: PART A TEST - toggle on/off --------------------------------------------
st.sidebar.header("Part A: VectorDB Test")
run_test = st.sidebar.checkbox("Run test search (Top 3 docs)", value=True)
test_query = st.sidebar.text_input("Test search string", value="Generative AI")

if run_test and test_query:
    context, sources = retrieve_context(test_query, collection, k=3)
    st.sidebar.write("Top 3 returned documents:")
    for i, src in enumerate(sources, start=1):
        st.sidebar.write(f"{i}, {src}")

# PART B - CHATBOT UI 
st.header("Course Information Chatbot (Hybrid RAG)")

st.caption(
    "This chatbot retrieves relevant syllabus text (RAG)."
    "If the answer is not in the PDFs, it will still answer using general knowledge and will say so." 
    
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_q = st.chat_input("Ask a question about the syllabi...")

if user_q:
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.write(user_q)

    with st.spinner("Retrieving course documents + generating answer..."):
        context, sources = retrieve_context(user_q, collection, k=3)
        answer = answer_with_hybrid_rag(user_q, context)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
        if sources:
            st.caption("Sources: " + ", ".join(sources))


