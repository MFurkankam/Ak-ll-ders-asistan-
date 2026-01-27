import logging
import os
import streamlit as st

from utils.auth import create_user, authenticate_user
from utils.app_state import (
    get_user_collection_name,
    get_anon_collection_name,
    migrate_anon_collection_to_user,
)
from utils.groq_client import GroqClient

logger = logging.getLogger(__name__)


def apply_global_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@400;600&display=swap');

        :root {
            --bg-0: #0b0f14;
            --bg-1: #0f141b;
            --bg-2: #161c25;
            --fg-0: #e6edf3;
            --fg-1: #c6d1dc;
            --muted: #9aa7b4;
            --accent: #4cc9f0;
            --accent-2: #80ed99;
            --warn: #ffb703;
        }

        .stApp {
            background: radial-gradient(1200px 600px at 15% -10%, #1a2230 0%, var(--bg-0) 60%);
            color: var(--fg-0);
            font-family: "IBM Plex Sans", sans-serif;
        }

        h1, h2, h3, h4 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: 0.3px;
        }

        .hero {
            padding: 1.5rem 1.75rem;
            background: linear-gradient(120deg, #141b24 0%, #0f141b 55%, #111925 100%);
            border: 1px solid #1f2a38;
            border-radius: 16px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
            margin-bottom: 1.5rem;
        }

        .hero h1 {
            margin-bottom: 0.5rem;
        }

        .hero p {
            color: var(--fg-1);
            margin: 0;
        }

        .card {
            padding: 1rem 1.1rem;
            background: var(--bg-1);
            border: 1px solid #1d2634;
            border-radius: 14px;
        }

        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(collection_name, show_sources=True):
    with st.sidebar:
        st.header("Hesap")
        render_auth()

        st.divider()

        render_nav()

        st.divider()

        st.header("API")
        render_groq_status()

        if show_sources:
            st.divider()
            st.subheader("Yüklenen Dosyalar")
            sources = st.session_state.rag_processor.get_all_sources(collection_name)
            if sources:
                for source in sources:
                    st.text(f"- {source}")
            else:
                st.info("Henüz dosya yüklenmedi")


def render_auth():
    if st.session_state.user is None:
        auth_options = ["Giriş Yap", "Kayıt Ol"]
        if st.session_state.get("pending_auth_tab"):
            st.session_state["auth_tab"] = auth_options[0]
            st.session_state.reg_success = True
            st.session_state.pending_auth_tab = False
        auth_tab = st.selectbox("Hesap", auth_options, key="auth_tab")
        if auth_tab == auth_options[0]:
            if st.session_state.get("reg_success"):
                st.success("Kayıt başarılı. Giriş yapabilirsiniz.")
                st.session_state.reg_success = False
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Parola", type="password", key="login_password")
            if st.button("Giriş Yap", key="login_btn"):
                try:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user = {
                            "id": user.id,
                            "email": user.email,
                            "role": user.role,
                            "full_name": user.full_name,
                        }
                        anon_collection_name = get_anon_collection_name()
                        if anon_collection_name:
                            migrate_anon_collection_to_user(
                                st.session_state.rag_processor,
                                anon_collection_name,
                                get_user_collection_name(user.id),
                            )
                        st.success("Giriş başarılı")
                        st.rerun()
                    else:
                        st.error("Email veya parola hatalı")
                except Exception:
                    logger.exception("Giris hatasi")
                    st.error("Giris yapilamadi. Lutfen tekrar deneyin.")
        else:
            reg_email = st.text_input("Email", key="reg_email")
            reg_name = st.text_input("Ad Soyad", key="reg_name")
            reg_password = st.text_input("Parola", type="password", key="reg_password")
            role_choice = st.selectbox("Rol", ["student", "teacher"], key="reg_role")
            if st.button("Kayıt Ol", key="reg_btn"):
                try:
                    create_user(
                        reg_email,
                        reg_password,
                        full_name=reg_name,
                        role=role_choice,
                    )
                    st.session_state.pending_auth_tab = True
                    st.rerun()
                except Exception:
                    logger.exception("Kayit hatasi")
                    st.error("Kayit tamamlanamadi. Lutfen tekrar deneyin.")
    else:
        name = st.session_state.user.get("full_name") or st.session_state.user.get("email")
        st.markdown(f"**Giriş yapan:** {name}")
        if st.button("Çıkış Yap", key="logout_btn"):
            st.session_state.user = None
            st.rerun()


def render_groq_status():
    env_key = os.getenv("GROQ_API_KEY")
    if env_key and not st.session_state.get("groq_api_key"):
        st.session_state.groq_api_key = env_key

    if st.session_state.groq_client is None:
        api_key = st.text_input(
            "GROQ API Key",
            type="password",
            key="groq_api_key_input",
            placeholder="gsk_...",
        )

        if st.button("Anahtarı Kaydet", key="save_groq_key"):
            if not api_key.strip():
                st.error("API anahtarı boş olamaz.")
            else:
                try:
                    st.session_state.groq_client = GroqClient(api_key.strip())
                    st.session_state.groq_api_key = api_key.strip()
                    st.success("API anahtarı kaydedildi.")
                    st.rerun()
                except Exception:
                    logger.exception("Groq API anahtari hatasi")
                    st.session_state.groq_client = None
                    st.error("API anahtari kaydedilemedi. Lutfen tekrar deneyin.")

        st.warning("GROQ_API_KEY ayarlanmadı. Anahtar girin veya ortam değişkeni ekleyin.")
    else:
        st.success("Groq API bağlantısı aktif")
        if st.button("Anahtarı Değiştir", key="reset_groq_key"):
            st.session_state.groq_client = None
            st.session_state.groq_api_key = None
            st.session_state.groq_api_key_input = ""
            st.rerun()


def render_nav():
    user = st.session_state.get("user")
    role = user.get("role") if user else "student"

    st.header("Menü")
    st.page_link("app.py", label="Ana Sayfa", icon="🏠")
    st.page_link("pages/1_Kutuphane.py", label="Kütüphane", icon="📚")
    st.page_link("pages/2_Soru_Cevap.py", label="Soru-Cevap", icon="💬")
    st.page_link("pages/3_Ozet.py", label="Özet", icon="🧾")
    st.page_link("pages/4_Quiz.py", label="Quiz", icon="📝")

    if role == "teacher":
        st.page_link("pages/5_Siniflar.py", label="Sınıflar", icon="🏫")
    else:
        st.page_link("pages/5_Siniflar.py", label="Sınıflarım", icon="🏫")
