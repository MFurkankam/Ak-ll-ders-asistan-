import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.classes import get_user_classes

st.set_page_config(
    page_title="Akıllı Ders Asistanı",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h1>Akıllı Ders Asistanı</h1>
        <p>RAG destekli özet, quiz ve sınıf yönetimi için tek merkez.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        "<div class='card'><b>1. Ders Notu Yükle</b><br/>PDF, DOCX, TXT dosyalarını ekle.</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        "<div class='card'><b>2. Özet ve Soru-Cevap</b><br/>İçerikten özet al veya soru sor.</div>",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        "<div class='card'><b>3. Quiz ve Sınıflar</b><br/>Quiz üret, sınıflarda paylaş.</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

sources = st.session_state.rag_processor.get_all_sources(collection_name)
left, right = st.columns([2, 1])
with left:
    st.subheader("Durum Özeti")
    st.write("Yüklenen dosya sayısı:", len(sources))
    if st.session_state.groq_client is None:
        st.warning("Groq API key girilmedi. Özet ve quiz için API key gerekli.")
    if not sources:
        st.info("Başlamak için önce dosya yükle sayfasına geç.")

with right:
    if st.session_state.user is not None:
        last_class_id = st.session_state.get("last_class_id")
        if last_class_id:
            classes = get_user_classes(st.session_state.user["id"])
            last_class = next((c for c in classes if c.id == last_class_id), None)
            if last_class:
                st.subheader("Son Etkileşim")
                if st.button(
                    f"{last_class.title}",
                    key="last_class_card",
                    use_container_width=True,
                ):
                    st.session_state.selected_class_id = last_class.id
                    st.session_state.show_class_detail = True
                    st.switch_page("pages/5_Siniflar.py")

    st.subheader("Hızlı Erişim")
    st.page_link("pages/1_Kutuphane.py", label="Kütüphane", icon="📚")
    st.page_link("pages/2_Soru_Cevap.py", label="Soru-Cevap", icon="💬")
    st.page_link("pages/4_Quiz.py", label="Quiz", icon="🧪")
    st.page_link("pages/5_Siniflar.py", label="Sınıflar", icon="🏫")
