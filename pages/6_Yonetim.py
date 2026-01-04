import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar

st.set_page_config(page_title="Yönetim", page_icon="\U0001f6e0", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name, show_sources=False)

st.markdown(
    """
    <div class="hero">
        <h2>Sistem Yönetimi</h2>
        <p>Veri durumu ve temizlik işlemleri.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Veritabanı Bilgileri")
    sources = st.session_state.rag_processor.get_all_sources(collection_name)
    st.metric("Yüklenen Dosya Sayısı", len(sources))
    if sources:
        for i, source in enumerate(sources, 1):
            st.write(f"{i}. {source}")

with col2:
    st.subheader("Tehlikeli İşlemler")
    st.warning("Bu işlemler geri alınamaz.")
    if st.button("Tüm Veritabanını Temizle", type="secondary"):
        if st.session_state.rag_processor.delete_collection(collection_name=collection_name):
            st.success("Veritabanı temizlendi")
            st.session_state.chat_history = []
            st.rerun()
        else:
            st.error("Veritabanı temizlenemedi")

st.divider()

st.subheader("Sistem Bilgileri")
st.info(
    """
    **Akıllı Ders Asistanı**

    - Yerel Vektör DB: ChromaDB
    - Cloud LLM: Groq API
    - Embedding Model: all-MiniLM-L6-v2
    - Desteklenen Formatlar: PDF, DOCX, TXT
    """
)
