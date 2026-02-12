# 1) SQLite patch for Chroma MUST BE FIRST
import sys
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

# 2) Imports
import time
import random
import re
import streamlit as st
from openai import OpenAI
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader


# ----------------------------
# Paths (your PDFs live here)
# ----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]              # repo root
PDF_FOLDER = BASE_DIR / "Labs" / "Lab-04-Data"              # ✅ your structure
CHROMA_DIR = Path("/tmp") / "ChromaDB_for_Lab"              # ✅ best for Streamlit Cloud


# ----------------------------
# UI
# ----------------------------
st.title("Lab 4: Course Info Chatbot (Hybrid RAG)")
st.caption(f"PDF folder: {PDF_FOLDER}")
st.caption(f"PDFs found: {[p.name for p in PDF_FOLDER.glob('*.pdf')]}")

st.divider()


# ----------------------------
# OpenAI client (store once)
# ----------------------------
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])


# ----------------------------
# Helpers
# ----------------------------
def safe_id_from_filename(pdf_file: Path) -> str:
    return pdf_file.stem.replace(" ", "_")


def extract_text_from_pdf(pdf_path: str, max_pages: int = 6) -> str:
    """
    Keep extraction light (syllabus info is usually early).
    This also reduces embedding payload size and failure risk.
    """
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages[:max_pages]:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)
    return "\n".join(pages_text).strip()


def embed_text_with_retry(
    text: str,
    model: str = "text-embedding-3-small",
    max_retries: int = 5,
) -> list:
    """
    Retries transient OpenAI server errors (HTTP 500).
    Caps text length to keep requests reliable.
    """
    client = st.session_state.openai_client
    text = (text or "")[:12000]  # cap chars

    for attempt in range(1, max_retries + 1):
        try:
            return client.embeddings.create(input=text, model=model).data[0].embedding
        except Exception:
            if attempt == max_retries:
                raise
            time.sleep((2 ** attempt) + random.random())


def build_vector_db_with_progress() -> "chromadb.api.models.Collection.Collection":
    """
    Lab requirement:
    - Construct Chroma collection named 'Lab4Collection'
    - Use OpenAI embeddings model 'text-embedding-3-small'
    - Use 7 PDFs -> text; use filename-derived key; metadata as needed
    - Store the collection in st.session_state.Lab4_VectorDB (caller does this)
    - Only build/embed if collection is empty
    """
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("Lab4Collection")

    # If already populated, don't rebuild (saves time/cost)
    if collection.count() > 0:
        return collection

    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))
    st.write("Indexing PDFs:", [p.name for p in pdf_files])

    added = 0
    progress = st.progress(0)
    status = st.empty()

    for i, pdf_file in enumerate(pdf_files, start=1):
        status.write(f"Indexing {i}/{len(pdf_files)}: {pdf_file.name}")

        text = extract_text_from_pdf(str(pdf_file))
        if not text:
            st.warning(f"Skipping {pdf_file.name} (no extractable text).")
            progress.progress(i / max(1, len(pdf_files)))
            continue

        doc_id = safe_id_from_filename(pdf_file)

        try:
            emb = embed_text_with_retry(text)
            collection.add(
                documents=[text[:12000]],            # keep stored doc size reasonable too
                ids=[doc_id],
                embeddings=[emb],
                metadatas=[{"source": pdf_file.name}],
            )
            added += 1
        except Exception as e:
            # Don't brick the whole build; continue indexing other PDFs
            st.error(f"Failed to add {pdf_file.name}: {e}")
            progress.progress(i / max(1, len(pdf_files)))
            continue

        progress.progress(i / max(1, len(pdf_files)))

    status.write("Indexing complete.")
    st.success(f"Loaded {added} PDFs into ChromaDB.")
    return collection


def retrieve_top_docs(query: str, collection, k: int = 3) -> list[str]:
    """Part A: return top-k PDF filenames (sources)."""
    q_emb = embed_text_with_retry(query)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"],  # compatible across Chroma versions
    )
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]

    sources = []
    for i in range(len(docs)):
        meta = metas[i] if i < len(metas) and metas[i] else {}
        sources.append(meta.get("source", f"doc_{i+1}"))
    return sources


def build_context_for_llm(query: str, collection, k: int = 7) -> tuple[str, list[str]]:
    """Part B: retrieve context for the LLM prompt."""
    q_emb = embed_text_with_retry(query)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"],
    )
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]

    # Optional: prioritize a specific course if mentioned (IST 195 etc.)
    m = re.search(r"\bIST\s*(\d{3})\b", query, re.IGNORECASE)
    course_code = f"IST {m.group(1)}" if m else None

    indexed = []
    for i in range(len(docs)):
        meta = metas[i] if i < len(metas) and metas[i] else {}
        src = meta.get("source", "")
        priority = 0 if (course_code and course_code.lower() in src.lower()) else 1
        indexed.append((priority, i))
    indexed.sort(key=lambda x: x[0])

    blocks, sources = [], []
    for _, i in indexed:
        meta = metas[i] if i < len(metas) and metas[i] else {}
        src = meta.get("source", f"doc_{i+1}")
        sources.append(src)
        blocks.append(f"[SOURCE: {src}]\n{docs[i]}")

    context = "\n\n---\n\n".join(blocks)[:12000]
    return context, sources


def answer_with_hybrid_rag(query: str, context: str) -> str:
    """
    Hybrid RAG:
    - Use syllabus excerpts if relevant (and say you used RAG + cite file names)
    - Otherwise answer with general knowledge and say it's not from the syllabi
    """
    client = st.session_state.openai_client

    messages = [
        {
            "role": "system",
            "content": (
                "You are a course information chatbot. "
                "You are given syllabus excerpts retrieved via Retrieval-Augmented Generation (RAG). "
                "If the answer is in the excerpts, you MUST use them and say you used course documents via RAG. "
                "If the answer is not in the excerpts, answer using general knowledge and clearly say it is not from the course documents."
            ),
        },
        {
            "role": "user",
            "content": f"""
QUESTION:
{query}

SYLLABUS EXCERPTS (RAG):
{context}
""".strip(),
        },
    ]

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content


# ----------------------------
# Maintenance / Reset
# ----------------------------
st.sidebar.header("Maintenance")
if st.sidebar.button("Delete & Rebuild Vector DB"):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        chroma_client.delete_collection("Lab4Collection")
    except Exception:
        pass
    st.session_state.pop("Lab4_VectorDB", None)
    st.success("Deleted Lab4Collection. Refresh the page, then click 'Build Vector DB'.")


# ----------------------------
# USER-FRIENDLY BUILD CONTROL (no endless spinner)
# ----------------------------
st.subheader("Vector DB Status")

if "Lab4_VectorDB" not in st.session_state:
    st.info("Vector database not built yet. Click **Build Vector DB** to index the PDFs (one-time).")

    if st.button("Build Vector DB"):
        start = time.time()
        with st.status("Indexing PDFs (one-time)...", expanded=True) as status:
            st.write("Reading PDFs…")
            st.write("Creating embeddings…")
            st.write("Saving into Chroma…")

            st.session_state.Lab4_VectorDB = build_vector_db_with_progress()

            elapsed = time.time() - start
            status.update(label=f"Vector DB ready ✅ ({elapsed:.1f}s)", state="complete", expanded=False)

else:
    st.success("Vector DB ready ✅")


# If DB not ready, stop before chat (prevents broken UX)
if "Lab4_VectorDB" not in st.session_state:
    st.warning("Build the Vector DB first to enable the chatbot.")
    st.stop()

collection = st.session_state.Lab4_VectorDB
st.write("Docs in collection:", collection.count())

st.divider()


# ----------------------------
# Part A (optional test)
# ----------------------------
st.sidebar.header("Part A Test")
test_query = st.sidebar.text_input("Test search", value="Generative AI")
if st.sidebar.button("Run Part A Test"):
    sources = retrieve_top_docs(test_query, collection, k=3)
    st.sidebar.write("Top 3 returned documents:")
    for i, s in enumerate(sources, start=1):
        st.sidebar.write(f"{i}. {s}")


# ----------------------------
# Part B: Chatbot UI
# ----------------------------
st.header("Course Information Chatbot (Hybrid RAG)")

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

    with st.spinner("Retrieving syllabus excerpts + generating answer..."):
        context, sources = build_context_for_llm(user_q, collection, k=7)
        answer = answer_with_hybrid_rag(user_q, context)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
        st.caption("Sources: " + ", ".join(sources))