import json
import streamlit as st

from utils.app_state import init_app, get_collection_name
from utils.ui import apply_global_styles, render_sidebar
from utils.classes import get_user_classes
from utils.quiz import create_quiz

st.set_page_config(page_title="Quiz", page_icon="\U0001f9ee", layout="wide")

init_app()
apply_global_styles()
collection_name = get_collection_name()
render_sidebar(collection_name)

st.markdown(
    """
    <div class="hero">
        <h2>Quiz Oluşturma</h2>
        <p>Notlardan otomatik sorular üret ve gerekirse sınıfa kaydet.</p>
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

col1, col2 = st.columns([3, 1])
with col1:
    quiz_topic = st.text_input(
        "Quiz konusu (opsiyonel)",
        placeholder="Örn: Veri yapıları",
    )
with col2:
    num_questions = st.number_input(
        "Soru sayısı",
        min_value=1,
        max_value=10,
        value=5,
    )

col3, col4 = st.columns(2)
with col3:
    quiz_type = st.selectbox(
        "Quiz Türü",
        ["Çoktan Seçmeli", "Doğru/Yanlış", "Boşluk Doldurma", "Kısa Cevap"],
        index=0,
    )
with col4:
    difficulty = st.selectbox(
        "Zorluk Seviyesi",
        ["Kolay", "Orta", "Zor"],
        index=1,
    )

if st.button("Quiz Oluştur", type="primary"):
    with st.spinner("Quiz oluşturuluyor..."):
        try:
            if quiz_topic:
                docs = st.session_state.rag_processor.search_documents(
                    quiz_topic,
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
                quiz_type_map = {
                    "Çoktan Seçmeli": "multiple_choice",
                    "Doğru/Yanlış": "true_false",
                    "Boşluk Doldurma": "fill_blank",
                    "Kısa Cevap": "short_answer",
                }
                difficulty_map = {
                    "Kolay": "kolay",
                    "Orta": "orta",
                    "Zor": "zor",
                }
                st.session_state.quiz_questions = st.session_state.groq_client.generate_quiz(
                    context,
                    num_questions,
                    quiz_type_map[quiz_type],
                    difficulty_map[difficulty],
                )
                st.session_state.quiz_generation += 1
                for key in list(st.session_state.keys()):
                    if key.startswith("keep_") or key.startswith("answer_"):
                        del st.session_state[key]
                if st.session_state.quiz_questions and 'error' not in st.session_state.quiz_questions[0]:
                    st.success(f"{len(st.session_state.quiz_questions)} soru oluşturuldu")
                    st.rerun()
                else:
                    st.error("Quiz oluşturulamadı.")
            else:
                st.error("İlgili içerik bulunamadı.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

if st.session_state.quiz_questions:
    st.markdown("---")
    st.subheader("Oluşturulan Sorular")
    selected = []
    for i, q in enumerate(st.session_state.quiz_questions, 1):
        q_type = q.get('type', 'multiple_choice')
        gen_key = st.session_state.quiz_generation
        if q_type == 'multiple_choice' or ('question' in q and 'A' in q):
            with st.expander(f"Soru {i}: {q.get('question', 'Soru bulunamadı')}", expanded=True):
                st.write(f"**A)** {q.get('A', '')}")
                st.write(f"**B)** {q.get('B', '')}")
                st.write(f"**C)** {q.get('C', '')}")
                st.write(f"**D)** {q.get('D', '')}")
                if st.button(f"Doğru Cevabı Göster", key=f"answer_{gen_key}_{i}"):
                    st.success(f"Doğru Cevap: **{q.get('correct_answer', 'A')}**")
                    if 'explanation' in q:
                        st.info(q['explanation'])
        elif q_type == 'true_false':
            with st.expander(f"Soru {i}: {q.get('statement', 'İfade bulunamadı')}", expanded=True):
                if st.button(f"Doğru Cevabı Göster", key=f"answer_{gen_key}_{i}"):
                    st.success(f"Doğru Cevap: **{q.get('correct_answer', 'Doğru')}**")
                    if 'explanation' in q:
                        st.info(q['explanation'])
        elif q_type == 'fill_blank':
            with st.expander(f"Soru {i}: Boşluğu doldur", expanded=True):
                st.write(q.get('sentence', 'Cümle bulunamadı'))
                if st.button(f"Doğru Cevabı Göster", key=f"answer_{gen_key}_{i}"):
                    st.success(f"Doğru Cevap: **{q.get('correct_answer', '')}**")
                    if 'explanation' in q:
                        st.info(q['explanation'])
        elif q_type == 'short_answer':
            with st.expander(f"Soru {i}: {q.get('question', 'Soru bulunamadı')}", expanded=True):
                if st.button(f"Örnek Cevabı Göster", key=f"answer_{gen_key}_{i}"):
                    st.success(f"Örnek Cevap: **{q.get('sample_answer', '')}**")
                    if 'keywords' in q and q['keywords']:
                        st.info(f"Anahtar Kelimeler: {', '.join(q['keywords'])}")

        keep = st.checkbox("Bu soruyu havuza ekle", key=f"keep_{gen_key}_{i}")
        if keep:
            selected.append(q)

    if selected:
        if st.button("Seçilenleri Havuzuna Ekle"):
            def _fingerprint(item):
                try:
                    return json.dumps(item, sort_keys=True, ensure_ascii=False)
                except Exception:
                    return str(item)

            existing = {_fingerprint(x) for x in st.session_state.quiz_bank}
            for item in selected:
                fp = _fingerprint(item)
                if fp not in existing:
                    st.session_state.quiz_bank.append(item)
                    existing.add(fp)
            st.success("Seçilen sorular havuza eklendi.")
            st.rerun()

    st.markdown("---")
    st.subheader("Quiz Kaydet")
    user = st.session_state.get('user')
    if user is None:
        st.info("Quiz kaydetmek için giriş yapmalısın.")
    else:
        classes = get_user_classes(user['id'])
        if not classes:
            st.info("Kaydetmek için bir sınıfın olması gerekiyor.")
        else:
            class_map = {f"{c.title} ({c.code})": c for c in classes}
            sel = st.selectbox("Sınıf seç", list(class_map.keys()))
            active_class = class_map.get(sel)
            save_title = st.text_input("Quiz Başlığı", value="Yeni Quiz")
            source_options = ["Yeni oluşturulan sorular"]
            if st.session_state.quiz_bank:
                source_options.append("Havuzdaki sorular")
            source_choice = st.radio("Quiz kaynağı", source_options, horizontal=True)

            if source_choice == "Havuzdaki sorular":
                save_list = st.session_state.quiz_bank
            else:
                save_list = st.session_state.quiz_questions

            if st.button("Quizi Kaydet"):
                try:
                    qlist = []
                    for gq in save_list:
                        qtype = gq.get('type') or gq.get('question_type') or 'mcq'
                        if qtype in ('multiple_choice', 'mcq'):
                            choices = {k: v for k, v in gq.items() if k in ('A', 'B', 'C', 'D')}
                            correct = gq.get('correct_answer') or gq.get('correct')
                            qlist.append({
                                'type': 'mcq',
                                'text': gq.get('question') or gq.get('question_text'),
                                'choices': choices,
                                'correct_answer': correct,
                                'topics': gq.get('topics', []),
                                'points': 1.0,
                            })
                        elif qtype == 'true_false':
                            qlist.append({
                                'type': 'true_false',
                                'text': gq.get('statement') or gq.get('question'),
                                'correct_answer': gq.get('correct_answer'),
                                'points': 1.0,
                            })
                        elif qtype == 'fill_blank':
                            qlist.append({
                                'type': 'fill_blank',
                                'text': gq.get('sentence'),
                                'correct_answer': gq.get('correct_answer'),
                                'points': 1.0,
                            })
                        else:
                            qlist.append({
                                'type': 'short_answer',
                                'text': gq.get('question'),
                                'correct_answer': gq.get('sample_answer') or gq.get('correct_answer'),
                                'topics': gq.get('keywords', []),
                                'points': 1.0,
                            })

                    created = create_quiz(
                        active_class.id,
                        save_title or 'Yeni Quiz',
                        user['id'],
                        qlist,
                    )
                    st.success(f"Quiz kaydedildi: {created.title}")
                    st.session_state.quiz_questions = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

    if st.session_state.quiz_bank:
        st.markdown("---")
        st.subheader("Soru Havuzu")
        st.write(f"Toplam soru: {len(st.session_state.quiz_bank)}")
        if st.button("Soru Havuzunu Temizle"):
            st.session_state.quiz_bank = []
            st.success("Soru havuzu temizlendi.")
            st.rerun()

    if st.button("Quizi Temizle"):
        st.session_state.quiz_questions = []
        st.rerun()
