# 1. SQLite patch for Chroma MUST BE FIRST
import sys
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

# 2. Imports
import re
import streamlit as st
from openai import OpenAI
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader


# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
PDF_FOLDER = BASE_DIR / "Labs" / "Lab-04-Data"          # your actual folder
CHROMA_DIR = Path("/tmp") / "ChromaDB_for_Lab"          # ✅ best for Streamlit Cloud

st.title("Lab 4: Chatbot Using RAG")

# Visible checks
st.caption(f"PDF folder: {PDF_FOLDER}")
st.caption(f"PDFs found: {[p.name for p in PDF_FOLDER.glob('*.pdf')]}")

# OpenAI client (store once)
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])


# ---------------- Helper functions ----------------
def safe_id_from_filename(pdf_file: Path) -> str:
    return pdf_file.stem.replace(" ", "_")


def extract_text_from_pdf(pdf_path: str, max_pages: int = 6) -> str:
    """Cap pages to avoid huge extraction / hangs; syllabus info is usually early."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages[:max_pages]:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)
    return "\n".join(pages_text).strip()


def add_to_collection(collection, text: str, doc_id: str, source_name: str) -> None:
    client = st.session_state.openai_client
    emb = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    ).data[0].embedding

    collection.add(
        documents=[text],
        ids=[doc_id],
        embeddings=[emb],
        metadatas=[{"source": source_name}],
    )


def load_pdfs_to_collection(folder_path: Path, collection) -> int:
    pdf_files = sorted(folder_path.glob("*.pdf"))
    st.write("PDFs to load:", [p.name for p in pdf_files])

    added_count = 0
    progress = st.progress(0)
    status = st.empty()

    for idx, pdf_file in enumerate(pdf_files, start=1):
        status.write(f"Processing {idx}/{len(pdf_files)}: {pdf_file.name}")

        try:
            text = extract_text_from_pdf(str(pdf_file))
        except Exception as e:
            st.error(f"PDF read failed for {pdf_file.name}: {e}")
            progress.progress(idx / max(1, len(pdf_files)))
            continue

        status.write(f"Extracted {len(text)} chars from {pdf_file.name}")

        if not text:
            st.warning(f"Skipping {pdf_file.name} (no extractable text).")
            progress.progress(idx / max(1, len(pdf_files)))
            continue

        doc_id = safe_id_from_filename(pdf_file)

        try:
            add_to_collection(collection, text, doc_id, pdf_file.name)
            added_count += 1
        except Exception as e:
            st.error(f"Failed to add {pdf_file.name}: {e}")
            # stop early so you see the real error
            break

        progress.progress(idx / max(1, len(pdf_files)))

    status.write("Done loading PDFs.")
    return added_count


def build_lab4_vectordb():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("Lab4Collection")

    if collection.count() == 0:
        loaded = load_pdfs_to_collection(PDF_FOLDER, collection)
        st.success(f"Loaded {loaded} PDFs into ChromaDB.")
    return collection


def retrieve_context(question: str, collection, k: int = 7):
    """Retrieve k docs. With whole-PDF embeddings, k=7 is fine for this lab."""
    if collection.count() == 0:
        return "", []

    client = st.session_state.openai_client
    q_emb = client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas"],   # keep compatible with your Chroma version
    )

    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    ids = (results.get("ids") or [[]])[0]  # may still exist

    # prioritize specific course if mentioned (IST 195, etc.)
    m = re.search(r"\bIST\s*(\d{3})\b", question, re.IGNORECASE)
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
        doc_id = ids[i] if i < len(ids) else f"doc_{i+1}"
        src = meta.get("source", doc_id)

        sources.append(src)
        blocks.append(f"[SOURCE: {src}]\n{docs[i]}")  # ✅ use docs[i], not docs[1]

    context = "\n\n---\n\n".join(blocks)
    context = context[:12000]  # cap prompt size
    return context, sources


def answer_with_hybrid_rag(question: str, context: str):
    client = st.session_state.openai_client

    messages = [
        {
            "role": "system",
            "content": (
                "You are a course information chatbot. "
                "You receive syllabus excerpts retrieved via RAG. "
                "If the answer is found in the excerpts, you MUST use them and cite the file name(s). "
                "If the answer is NOT found in the excerpts, you may answer using general knowledge, "
                "but clearly state that it is not from the syllabus excerpts."
            ),
        },
        {
            "role": "user",
            "content": f"""
QUESTION:
{question}

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


# ---------------- Build/reuse VectorDB ----------------
if "Lab4_VectorDB" not in st.session_state:
    with st.spinner("Building Lab4 vector DB (first run only)..."):
        st.session_state.Lab4_VectorDB = build_lab4_vectordb()

collection = st.session_state.Lab4_VectorDB
st.write("Docs in collection:", collection.count())


# Maintenance (optional)
st.sidebar.header("Maintenance")
if st.sidebar.button("Rebuild VectorDB"):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        chroma_client.delete_collection("Lab4Collection")
    except Exception:
        pass
    st.session_state.pop("Lab4_VectorDB", None)
    st.success("Deleted collection. Refresh the page to rebuild from PDFs.")


# ---------------- Part A test (optional) ----------------
st.sidebar.header("Part A: VectorDB Test")
run_test = st.sidebar.checkbox("Run test search (Top docs)", value=False)
test_query = st.sidebar.text_input("Test search string", value="Generative AI")

if run_test and test_query:
    context, sources = retrieve_context(test_query, collection, k=7)
    st.sidebar.write("Returned documents:")
    for i, src in enumerate(sources, start=1):
        st.sidebar.write(f"{i}. {src}")


# ---------------- Chat UI ----------------
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

    with st.spinner("Retrieving course documents + generating answer..."):
        context, sources = retrieve_context(user_q, collection, k=7)
        answer = answer_with_hybrid_rag(user_q, context)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
        if sources:
            st.caption("Sources: " + ", ".join(sources))
