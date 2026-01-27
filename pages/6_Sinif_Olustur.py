import logging
import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.classes import create_class

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Sınıf Oluştur", page_icon="➕", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name, show_sources=False)

if st.session_state.user is None:
    st.info("Lütfen önce giriş yap.")
    st.stop()

user_role = st.session_state.user.get("role", "student")

if st.button("< Sınıflar", type="secondary"):
    st.switch_page("pages/5_Siniflar.py")

st.markdown(
    """
    <div class="hero">
        <h2>Sınıf Oluştur</h2>
        <p>Sınıf başlığı ve açıklamasını girerek yeni sınıf oluştur.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if user_role != "teacher":
    st.info("Sınıf oluşturma sadece öğretmen hesapları için kullanılabilir.")
    st.stop()

class_title = st.text_input("Sınıf Başlığı")
class_desc = st.text_area("Açıklama")

if st.button("Oluştur", type="primary"):
    if not class_title.strip():
        st.error("Sınıf başlığı boş olamaz.")
    else:
        try:
            cls = create_class(
                class_title.strip(),
                class_desc.strip(),
                st.session_state.user["id"],
            )
            st.success(f"Sınıf oluşturuldu. Davet kodu: {cls.code}")
            st.session_state.selected_class_id = cls.id
            st.session_state.show_class_detail = True
            st.session_state.last_class_id = cls.id
            st.switch_page("pages/5_Siniflar.py")
        except Exception:
            logger.exception("Sinif olusturma hatasi")
            st.error("Sinif olusturulamadi. Lutfen tekrar deneyin.")
