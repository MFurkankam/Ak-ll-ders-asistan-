import logging
import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Kütüphane", page_icon="📚", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h2>Kütüphane</h2>
        <p>Dosya yükleme ve veri yönetimi tek sayfada.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Ders Notu Yükleme")
uploaded_file = st.file_uploader(
    "Dosya seç",
    type=["pdf", "docx", "txt"],
    help="Desteklenen formatlar: PDF, DOCX, TXT",
)

if uploaded_file is not None:
    st.info(f"Seçilen dosya: {uploaded_file.name}")
    if st.button("Dosyayı Yükle ve Kaydet", type="primary"):
        with st.spinner("Dosya işleniyor..."):
            try:
                documents = st.session_state.rag_processor.process_document(
                    uploaded_file,
                    uploaded_file.name,
                )
                st.session_state.rag_processor.add_documents_to_vectorstore(
                    documents,
                    collection_name=collection_name,
                )
                st.success(f"{uploaded_file.name} başarıyla yüklendi ve işlendi.")
                st.success(f"{len(documents)} metin parçası oluşturuldu.")
                st.rerun()
            except Exception:
                logger.exception("Dosya yukleme hatasi")
                st.error("Dosya yuklenemedi. Lutfen tekrar deneyin.")

st.markdown("---")

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
