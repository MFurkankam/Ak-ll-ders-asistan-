import logging
import streamlit as st
from datetime import datetime
from xml.sax.saxutils import escape

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.summaries import create_summary, get_summaries_for_user, delete_summary

logger = logging.getLogger(__name__)


def _summary_to_xml(title: str, created_at: str, content: str) -> str:
    title_xml = escape(title or "")
    date_xml = escape(created_at or "")
    content_xml = escape(content or "")
    return (
        "<summary>"
        f"<title>{title_xml}</title>"
        f"<created_at>{date_xml}</created_at>"
        f"<content>{content_xml}</content>"
        "</summary>"
    )

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

selected_sources = st.multiselect("Kaynak filtrele (opsiyonel)", options=sources)

col1, col2 = st.columns([2, 1])
with col1:
    summary_topic = st.text_input(
        "Özet konusu (opsiyonel)",
        placeholder="Örn: Python programlama temelleri",
    )
with col2:
    detail_level = st.selectbox(
        "Özet detay seviyesi",
        ["kısa", "orta", "detaylı", "çok detaylı"],
        index=1,
    )

if st.button("Özet Oluştur", type="primary"):
    with st.spinner("Özet oluşturuluyor..."):
        try:
            sources_count = len(selected_sources) if selected_sources else len(sources)
            if summary_topic:
                k = st.session_state.rag_processor.get_dynamic_k(summary_topic, sources_count)
                docs = st.session_state.rag_processor.search_documents(
                    summary_topic,
                    k=k,
                    collection_name=collection_name,
                    source_filter=selected_sources or None,
                )
            else:
                k = st.session_state.rag_processor.get_dynamic_k("genel bilgi", sources_count)
                docs = st.session_state.rag_processor.search_documents(
                    "genel bilgi",
                    k=k,
                    collection_name=collection_name,
                    source_filter=selected_sources or None,
                )

            if docs:
                context = "\n\n".join([doc.page_content for doc in docs])
                summary = st.session_state.groq_client.generate_summary(
                    context,
                    detail_level,
                )
                st.success("Ozet basariyla olusturuldu")
                st.markdown("---")
                st.markdown(summary)

                title = summary_topic.strip() if summary_topic else "Genel Ozet"
                st.session_state.last_summary = {
                    "title": title,
                    "content": summary,
                    "created_at": datetime.now().date().isoformat(),
                }
            else:
                st.error("Ilgili icerik bulunamadi.")
        except Exception:
            logger.exception("Ozet olusturma hatasi")
            st.error("Ozet olusturulamadi. Lutfen tekrar deneyin.")

if st.session_state.get("last_summary"):
    st.info("Bu ozeti kaydetmek ister misiniz?")
    if st.session_state.user is None:
        st.warning("Ozetleri kalici kaydetmek icin giris yapmalisin.")
    elif st.button("Ozetimi Kaydet", key="save_summary_btn"):
        item = st.session_state.last_summary
        create_summary(
            st.session_state.user["id"],
            item.get("title") or "Genel Ozet",
            item.get("content") or "",
        )
        st.session_state.last_summary = None
        st.success("Ozet kaydedildi.")
        st.rerun()

st.markdown("---")
st.subheader("Ozetlerim")
if st.session_state.user is None:
    st.info("Kaydedilmis ozetleri gormek icin giris yapmalisin.")
else:
    saved = get_summaries_for_user(st.session_state.user["id"])
    if saved:
        for idx, item in enumerate(saved, start=1):
            title = item.title or f"Ozet {idx}"
            created_at = (
                item.created_at.date().isoformat() if item.created_at else ""
            )
            with st.expander(f"{title} ({created_at})"):
                col_a, col_b, col_c = st.columns([0.85, 0.075, 0.075])
                with col_a:
                    st.write(item.content or "")
                with col_b:
                    if st.button("\U0001F5D1", key=f"del_summary_{item.id}", help="Ozeti sil"):
                        delete_summary(item.id, st.session_state.user["id"])
                        st.rerun()
                with col_c:
                    xml_data = _summary_to_xml(title, created_at, item.content or "")
                    st.download_button(
                        "\u2B07",
                        data=xml_data,
                        file_name=f"summary_{item.id}.xml",
                        mime="application/xml",
                        key=f"dl_summary_{item.id}",
                        help="XML indir",
                    )
    else:
        st.info("Henuz kaydedilmis ozet yok.")
