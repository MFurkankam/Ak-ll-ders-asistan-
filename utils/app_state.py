import os
import uuid
import streamlit as st

from utils.logging_config import setup_logging

from utils.db import init_db
from utils.rag_processor import RAGProcessor
from utils.groq_client import GroqClient


def init_app():
    setup_logging()
    init_db()

    if "rag_processor" not in st.session_state:
        st.session_state.rag_processor = RAGProcessor()

    if "user" not in st.session_state:
        st.session_state.user = None

    if "groq_client" not in st.session_state:
        groq_api_key = os.getenv("GROQ_API_KEY")
        st.session_state.groq_client = GroqClient(groq_api_key) if groq_api_key else None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []

    if "quiz_bank" not in st.session_state:
        st.session_state.quiz_bank = []

    if "quiz_generation" not in st.session_state:
        st.session_state.quiz_generation = 0

    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    if "saved_summaries" not in st.session_state:
        st.session_state.saved_summaries = []


def get_user_collection_name(user_id: int) -> str:
    return f"ders_notlari_user_{user_id}"


def get_anon_collection_name():
    anon_id = st.session_state.get("anon_collection_id")
    if not anon_id:
        return None
    return f"ders_notlari_anon_{anon_id}"


def get_collection_name():
    user = st.session_state.get("user")
    if user and user.get("id") is not None:
        return get_user_collection_name(user["id"])
    if "anon_collection_id" not in st.session_state:
        st.session_state.anon_collection_id = uuid.uuid4().hex
    return get_anon_collection_name()


def migrate_anon_collection_to_user(rag_processor, anon_collection_name, user_collection_name):
    if not anon_collection_name:
        return 0
    source = rag_processor.get_collection(anon_collection_name)
    if source is None:
        return 0
    data = source.get()
    docs = data.get("documents") or []
    if not docs:
        return 0
    metadatas = data.get("metadatas")
    if metadatas and len(metadatas) == len(docs):
        meta_for_ids = metadatas
    else:
        metadatas = None
        meta_for_ids = [{} for _ in docs]
    ids = [
        f"{(meta or {}).get('source', 'unknown')}_{uuid.uuid4().hex}"
        for meta in meta_for_ids
    ]
    target = rag_processor.chroma_client.get_or_create_collection(
        name=user_collection_name,
        embedding_function=rag_processor.embedding_function,
    )
    try:
        if metadatas is None:
            target.add(documents=docs, ids=ids)
        else:
            target.add(documents=docs, metadatas=metadatas, ids=ids)
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Anon koleksiyon tasima hatasi")
        return 0
    rag_processor.delete_collection(collection_name=anon_collection_name)
    return len(docs)
