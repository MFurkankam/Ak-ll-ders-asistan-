import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar

st.set_page_config(page_title="Soru-Cevap", page_icon="\U0001f4ac", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h2>Ders Notları Hakkında Soru Sor</h2>
        <p>Yüklediğin ders notlarından bağlamlı cevaplar al.</p>
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

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_question = st.chat_input("Sorunu yaz...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)

    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question,
    })

    with st.spinner("Cevap hazırlanıyor..."):
        relevant_docs = st.session_state.rag_processor.search_documents(
            user_question,
            k=4,
            collection_name=collection_name,
        )
        if relevant_docs:
            answer = st.session_state.groq_client.answer_question(
                user_question,
                relevant_docs,
            )
        else:
            answer = (
                "Bu konuda notlarında ilgili bilgi bulamadım. "
                "Farklı bir soru sorabilir ya da daha fazla not yükleyebilirsin."
            )

    with st.chat_message("assistant"):
        st.write(answer)

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
    })

if st.session_state.chat_history:
    if st.button("Chat Geçmişini Temizle"):
        st.session_state.chat_history = []
        st.rerun()
