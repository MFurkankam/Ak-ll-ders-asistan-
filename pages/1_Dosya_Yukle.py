import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar

st.set_page_config(page_title="Dosya Yükle", page_icon="\U0001f4e5", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h2>Ders Notu Yükleme</h2>
        <p>PDF, DOCX veya TXT formatında ders notlarını yükle.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Dosya seç",
    type=["pdf", "docx", "txt"],
    help="Desteklenen formatlar: PDF, DOCX, TXT",
)

if uploaded_file is not None:
    st.info(f"Seçilen dosya: {uploaded_file.name}")
    if st.button("Dosyayı İşle ve Kaydet", type="primary"):
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
            except Exception as e:
                st.error(f"Hata: {str(e)}")
