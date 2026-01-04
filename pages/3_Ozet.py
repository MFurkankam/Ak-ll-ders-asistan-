import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar

st.set_page_config(page_title="Özet", page_icon="\U0001f4dd", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h2>Ders Notu Özetleme</h2>
        <p>Notlarını kısa, orta ya da detaylı özetle.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.groq_client is None:
    st.error("Önce Groq API Key girmen gerekiyor.")
    st.stop()

sources = st.session_state.rag_processor.get_all_sources(collection_name)
if not sources:
    st.warning("Henüz dosya yüklenmedi. Önce dosya yükle sayfasına git.")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    summary_topic = st.text_input(
        "Özet konusu (opsiyonel)",
        placeholder="Örn: Python programlama temelleri",
    )
with col2:
    detail_level = st.selectbox(
        "Özet detay seviyesi",
        ["kısa", "orta", "detaylı"],
        index=1,
    )

if st.button("Özet Oluştur", type="primary"):
    with st.spinner("Özet oluşturuluyor..."):
        try:
            if summary_topic:
                docs = st.session_state.rag_processor.search_documents(
                    summary_topic,
                    k=6,
                    collection_name=collection_name,
                )
            else:
                docs = st.session_state.rag_processor.search_documents(
                    "genel bilgi",
                    k=6,
                    collection_name=collection_name,
                )

            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                summary = st.session_state.groq_client.generate_summary(
                    context,
                    detail_level,
                )
                st.success("Özet başarıyla oluşturuldu")
                st.markdown("---")
                st.markdown(summary)
            else:
                st.error("İlgili içerik bulunamadı.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")
