# 1) SQLite patch for Chroma MUST BE FIRST
import sys
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

# 2) Imports
import time
import random
import streamlit as st
from openai import OpenAI
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader


# ----------------------------
# App UI
# ----------------------------
st.title("Lab 4: Course Info Chatbot (RAG)")


# ----------------------------
# Paths (your PDFs live here)
# ----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]              # repo root
PDF_FOLDER = BASE_DIR / "Labs" / "Lab-04-Data"              # ✅ your structure
CHROMA_DIR = Path("/tmp") / "ChromaDB_for_Lab"              # ✅ best for Streamlit Cloud


# ----------------------------
# OpenAI client
# ----------------------------
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])


# ----------------------------
# Helpers
# ----------------------------
def safe_id_from_filename(pdf_file: Path) -> str:
    return pdf_file.stem.replace(" ", "_")


def extract_text_from_pdf(pdf_path: str, max_pages: int = 6) -> str:
    """Keep extraction light (syllabus header info is usually early)."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages[:max_pages]:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)
    return "\n".join(pages_text).strip()


def embed_text_with_retry(text: str, model: str = "text-embedding-3-small", max_retries: int = 5):
    """Retries transient OpenAI 500 errors."""
    client = st.session_state.openai_client

    # Keep request small & reliable
    text = text[:12000]

    for attempt in range(1, max_retries + 1):
        try:
            return client.embeddings.create(input=text, model=model).data[0].embedding
        except Exception as e:
            if attempt == max_retries:
                raise
            # exponential backoff + jitter
            time.sleep((2 ** attempt) + random.random())


def build_vector_db():
    """
    Lab requirement:
    - Construct ChromaDB collection named 'Lab4Collection'
    - Store in st.session_state.Lab4_VectorDB
    - Only build once
    """
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("Lab4Collection")

    # Only populate if empty
    if collection.count() > 0:
        return collection

    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))
    st.write("PDFs found:", [p.name for p in pdf_files])

    added = 0
    progress = st.progress(0)
    status = st.empty()

    for i, pdf_file in enumerate(pdf_files, start=1):
        status.write(f"Embedding {i}/{len(pdf_files)}: {pdf_file.name}")

        text = extract_text_from_pdf(str(pdf_file))
        if not text:
            st.warning(f"Skipping {pdf_file.name} (no extractable text).")
            progress.progress(i / len(pdf_files))
            continue

        doc_id = safe_id_from_filename(pdf_file)

        try:
            emb = embed_text_with_retry(text)
            collection.add(
                documents=[text],
                ids=[doc_id],
                embeddings=[emb],
                metadatas=[{"source": pdf_file.name}],
            )
            added += 1
        except Exception as e:
            # Do NOT brick the whole build; continue embedding the rest
            st.error(f"Failed to embed {pdf_file.name}: {e}")
            continue

        progress.progress(i / len(pdf_files))

    status.write("Vector DB build complete.")
    st.success(f"Loaded {added} PDFs into ChromaDB.")
    return collection


def retrieve_top_docs(query: str, collection, k: int = 3):
    """Part A test retrieval: return top filenames (sources)."""
    q_emb = embed_text_with_retry(query)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"],   # compatible across Chroma versions
    )

    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]

    sources = []
    for idx in range(len(docs)):
        meta = metas[idx] if idx < len(metas) and metas[idx] else {}
        sources.append(meta.get("source", f"doc_{idx+1}"))

    return results, sources


def build_context_for_llm(query: str, collection, k: int = 7):
    """Part B: retrieve context to send to the LLM."""
    q_emb = embed_text_with_retry(query)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"],
    )

    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]

    blocks = []
    sources = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) and metas[i] else {}
        src = meta.get("source", f"doc_{i+1}")
        sources.append(src)
        blocks.append(f"[SOURCE: {src}]\n{doc}")

    context = "\n\n---\n\n".join(blocks)[:12000]
    return context, sources


def answer_with_rag(query: str, context: str):
    """Hybrid RAG: uses PDFs when helpful, otherwise answers generally."""
    client = st.session_state.openai_client

    messages = [
        {
            "role": "system",
            "content": (
                "You are a course information chatbot. "
                "You are given syllabus excerpts retrieved via RAG. "
                "If the answer is in the excerpts, use them and say you used course documents via RAG. "
                "If the answer is not in the excerpts, answer using general knowledge and clearly say it is not from the course documents."
            )
        },
        {
            "role": "user",
            "content": f"""
QUESTION:
{query}

SYLLABUS EXCERPTS (RAG):
{context}
""".strip()
        }
    ]

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3
    )
    return resp.choices[0].message.content


# ----------------------------
# Rebuild button (start fresh)
# ----------------------------
st.sidebar.header("Maintenance")
if st.sidebar.button("Rebuild Lab4Collection"):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        chroma_client.delete_collection("Lab4Collection")
    except Exception:
        pass
    st.session_state.pop("Lab4_VectorDB", None)
    st.success("Deleted collection. Refresh the page to rebuild.")


# ----------------------------
# Build DB ONCE per session
# ----------------------------
if "Lab4_VectorDB" not in st.session_state:
    with st.spinner("Building Lab4 vector DB (first run only)..."):
        st.session_state.Lab4_VectorDB = build_vector_db()

collection = st.session_state.Lab4_VectorDB
st.write("Docs in collection:", collection.count())


# ----------------------------
# Part A: Test the vectorDB
# ----------------------------
st.sidebar.header("Part A Test")
test_query = st.sidebar.text_input("Test search", value="Generative AI")

if st.sidebar.button("Run Part A Test"):
    _, sources = retrieve_top_docs(test_query, collection, k=3)
    st.write("Top 3 returned documents:")
    for i, s in enumerate(sources, start=1):
        st.write(f"{i}. {s}")


# ----------------------------
# Part B: Chatbot
# ----------------------------
st.header("Part B: Course Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_q = st.chat_input("Ask a question about the syllabi...")

if user_q:
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.write(user_q)

    with st.spinner("Retrieving syllabi + generating answer..."):
        context, sources = build_context_for_llm(user_q, collection, k=7)
        answer = answer_with_rag(user_q, context)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
        st.caption("Sources: " + ", ".join(sources))
