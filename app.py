import streamlit as st
import os
from utils.rag_processor import RAGProcessor
from utils.groq_client import GroqClient
import json, io, csv

# Sayfa yapılandırması
st.set_page_config(
    page_title="Akıllı Ders Asistanı",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    </style>
""", unsafe_allow_html=True)

# Database init and Session state başlatma
from utils.db import init_db, get_session
from utils.auth import create_user, authenticate_user, get_user_by_id

# Initialize DB
init_db()

if 'rag_processor' not in st.session_state:
    st.session_state.rag_processor = RAGProcessor()

# Auth session
if 'user' not in st.session_state:
    st.session_state.user = None

if 'groq_client' not in st.session_state:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        st.session_state.groq_client = GroqClient(groq_api_key)
    else:
        st.session_state.groq_client = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# Sidebar auth UI
with st.sidebar:
    if st.session_state.user is None:
        auth_tab = st.selectbox("Hesap", ["Giriş Yap","Kayıt Ol"], key="auth_tab")
        if auth_tab == "Giriş Yap":
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Parola", type="password", key="login_password")
            if st.button("Giriş Yap", key="login_btn"):
                try:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.user = {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}
                        st.success("Giriş başarılı")
                        st.experimental_rerun()
                    else:
                        st.error("Email veya parola yanlış")
                except Exception as e:
                    st.error(f"Hata: {e}")
        else:
            reg_email = st.text_input("Email", key="reg_email")
            reg_name = st.text_input("Ad Soyad", key="reg_name")
            reg_password = st.text_input("Parola", type="password", key="reg_password")
            role_choice = st.selectbox("Rol", ["student","teacher"], key="reg_role")
            if st.button("Kayıt Ol", key="reg_btn"):
                try:
                    user = create_user(reg_email, reg_password, full_name=reg_name, role=role_choice)
                    st.success("Kayıt başarılı. Giriş yapabilirsiniz.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
    else:
        st.markdown(f"**Giriş yapan:** {st.session_state.user.get('full_name') or st.session_state.user.get('email')}")
        if st.button("Çıkış Yap", key="logout_btn"):
            st.session_state.user = None
            st.experimental_rerun()

# Başlık
st.markdown('<h1 class="main-header">📚 Akıllı Ders Asistanı</h1>', unsafe_allow_html=True)
st.markdown("### RAG Destekli Ders Notu Özetleme ve Quiz Oluşturma Sistemi")

# Sidebar - Menü
with st.sidebar:
    st.header("🎯 Menü")
    
    # Groq API Key kontrolü
    if st.session_state.groq_client is None:
        st.warning("⚠️ GROQ_API_KEY ayarlanmamış!")
        groq_key_input = st.text_input("Groq API Key", type="password")
        if st.button("API Key'i Kaydet"):
            if groq_key_input:
                try:
                    st.session_state.groq_client = GroqClient(groq_key_input)
                    st.success("✅ API Key kaydedildi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {str(e)}")
    else:
        st.success("✅ Groq API bağlantısı aktif")
    
    st.divider()
    
    menu_option = st.radio(
        "Bir işlem seçin:",
        ["📤 Dosya Yükle", "🏫 Sınıflar", "💬 Soru-Cevap", "📝 Özet Oluştur", "🎯 Quiz Oluştur", "📊 Yönetim"],
        index=0
    )
    
    st.divider()
    
    # Yüklenmiş dosyalar
    st.subheader("📁 Yüklenmiş Dosyalar")
    sources = st.session_state.rag_processor.get_all_sources()
    if sources:
        for source in sources:
            st.text(f"✓ {source}")
    else:
        st.info("Henüz dosya yüklenmedi")

# Ana içerik alanı
if st.session_state.groq_client is None and menu_option != "📤 Dosya Yükle":
    st.error("🔑 Lütfen önce Groq API Key'inizi girin!")
else:
    # Sınıflar
    if menu_option == "🏫 Sınıflar":
        st.header("🏫 Sınıf Yönetimi")
        if st.session_state.user is None:
            st.info("Lütfen önce giriş yapın.")
        else:
            from utils.classes import create_class, join_class_by_code, get_user_classes
            from utils.quiz import get_quizzes_for_class, create_quiz, publish_quiz, get_questions_for_quiz, grade_attempt

            st.subheader("Sınıf Oluştur")
            col1, col2 = st.columns([3,1])
            with col1:
                class_title = st.text_input("Sınıf başlığı")
                class_desc = st.text_area("Açıklama")
            with col2:
                if st.button("Oluştur"):
                    try:
                        cls = create_class(class_title, class_desc, st.session_state.user['id'])
                        st.success(f"Sınıf oluşturuldu! Davet kodu: {cls.code}")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")

            st.subheader("Sınıfa Katıl")
            join_code = st.text_input("Davet kodu ile katıl")
            if st.button("Katıl"):
                try:
                    enroll = join_class_by_code(join_code, st.session_state.user['id'])
                    st.success("Sınıfa başarıyla katıldınız!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

            st.subheader("Üyeliğim Olan Sınıflar")
            classes = get_user_classes(st.session_state.user['id'])
            if classes:
                # select class to manage
                class_map = {f"{c.title} ({c.code})": c for c in classes}
                sel = st.selectbox("Bir sınıf seçin", list(class_map.keys()))
                active_class = class_map.get(sel)

                st.write(f"**{active_class.title}** — Kod: `{active_class.code}`")
                st.write(active_class.description or "")

                # If user is owner or a teacher, show management tools
                can_manage = (st.session_state.user.get('role') == 'teacher') or (active_class.owner_id == st.session_state.user.get('id'))

                if can_manage:
                    st.markdown("---")
                    st.subheader("Sınıf İçin Quiz Yönetimi")

                    # Show existing quizzes
                    quizzes = get_quizzes_for_class(active_class.id)
                    if quizzes:
                        for q in quizzes:
                            with st.expander(f"{q.title} — {'Yayınlandı' if q.published else 'Taslak'}"):
                                st.write(f"Oluşturan: {q.author_id} — Oluşturuldu: {q.created_at}")
                                col_a, col_b = st.columns([1,1])
                                with col_a:
                                    if st.button("Yayınla" if not q.published else "Yayını Kapat", key=f"pub_{q.id}"):
                                        try:
                                            publish_quiz(q.id, publish=not q.published)
                                            st.success("Durum güncellendi")
                                            st.experimental_rerun()
                                        except Exception as e:
                                            st.error(f"Hata: {e}")
                                with col_b:
                                    if st.button("Soruları Görüntüle", key=f"view_{q.id}"):
                                        questions = get_questions_for_quiz(q.id)
                                        for qq in questions:
                                            st.write(f"- ({qq.type}) {qq.text} [{qq.points} puan]")
                    else:
                        st.info("Henüz bu sınıfa ait quiz yok.")

                    st.markdown("---")
                    st.subheader("Otomatik Oluşturulan Quiz'i Kaydet")
                    if st.session_state.quiz_questions:
                        save_title = st.text_input("Quiz Başlığı (Kaydetmek için) ")
                        if st.button("Quizi Kaydet"):
                            try:
                                # transform generated questions into DB format
                                qlist = []
                                for gq in st.session_state.quiz_questions:
                                    qtype = gq.get('type') or gq.get('question_type') or 'mcq'
                                    if qtype in ('multiple_choice','mcq'):
                                        choices = {k:v for k,v in gq.items() if k in ('A','B','C','D')}
                                        correct = gq.get('correct_answer') or gq.get('correct')
                                        qlist.append({'type':'mcq','text': gq.get('question') or gq.get('question_text'),'choices':choices,'correct_answer':correct,'topics': gq.get('topics',[]),'points':1.0})
                                    elif qtype == 'true_false':
                                        qlist.append({'type':'true_false','text': gq.get('statement') or gq.get('question'),'correct_answer': gq.get('correct_answer'),'points':1.0})
                                    elif qtype == 'fill_blank':
                                        qlist.append({'type':'fill_blank','text': gq.get('sentence'),'correct_answer': gq.get('correct_answer'),'points':1.0})
                                    else:
                                        qlist.append({'type':'short_answer','text': gq.get('question'),'correct_answer': gq.get('sample_answer') or gq.get('correct_answer'),'topics': gq.get('keywords',[]),'points':1.0})

                                created = create_quiz(active_class.id, save_title or 'Yeni Quiz', st.session_state.user['id'], qlist)
                                st.success(f"Quiz kaydedildi: {created.title}")
                                st.session_state.quiz_questions = []
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                    else:
                        st.info("Kaydetmek için otomatik oluşturulmuş bir quiz yok. Quiz Oluştur menüsünden önce otomatik quiz oluşturun.")

                    st.markdown("---")
                    st.subheader("Konu Başarı Durumu")
                    from utils.quiz import compute_topic_mastery, get_attempts_for_class
                    topic_stats = compute_topic_mastery(active_class.id)
                    if topic_stats:
                        for topic, data in topic_stats.items():
                            st.write(f"- **{topic}**: %{data['mastery']*100:.1f} ({data['correct']}/{data['attempts']})")
                        weak = [t for t,d in topic_stats.items() if d['attempts']>=3 and d['mastery'] < 0.6]
                        if weak:
                            st.warning("🔻 Zayıf konular: " + ", ".join(weak))
                    else:
                        st.info("Henüz deneme verisi yok.")

                    st.subheader("Denemeler")
                    # Filters
                    quiz_opts = ['Tüm quizler'] + [q.title for q in quizzes]
                    sel_quiz_title = st.selectbox("Quiz", quiz_opts, index=0, key=f"quiz_filter_{active_class.id}")
                    sel_quiz_id = None
                    if sel_quiz_title != 'Tüm quizler':
                        sel_quiz_id = [q for q in quizzes if q.title == sel_quiz_title][0].id

                    # gather current attempts for student list
                    all_attempts = get_attempts_for_class(active_class.id)
                    student_opts = ['Tümü'] + sorted({a['user_email'] for a in all_attempts})
                    sel_student = st.selectbox("Öğrenci", student_opts, index=0, key=f"student_filter_{active_class.id}")
                    sel_student_email = None if sel_student == 'Tümü' else sel_student

                    col_a, col_b = st.columns(2)
                    with col_a:
                        date_range = st.date_input("Tarih aralığı", key=f"date_filter_{active_class.id}")
                    with col_b:
                        if st.button("Filtrele"):
                            st.experimental_rerun()

                    since = None
                    until = None
                    if isinstance(date_range, list) and len(date_range) == 2:
                        since = date_range[0].isoformat()
                        until = date_range[1].isoformat()

                    attempts = get_attempts_for_class(active_class.id, quiz_id=sel_quiz_id, user_email=sel_student_email, since=since, until=until)

                    if attempts:
                        # Topic mastery for filtered attempts
                        topic_stats_filtered = compute_topic_mastery(active_class.id, attempts=attempts)
                        if topic_stats_filtered:
                            st.markdown('---')
                            st.subheader('Konu Başarı Grafiği')
                            chart_data = {k: v['mastery']*100 for k,v in topic_stats_filtered.items()}
                            st.bar_chart(list(chart_data.values()), use_container_width=True)
                            cols = list(chart_data.keys())
                            if cols:
                                st.write(', '.join([f"{k}: %{v:.1f}" for k,v in chart_data.items()]))

                        # CSV export (filtered)
                        if st.button("CSV Olarak İndir (Filtreli)"):
                            output = io.StringIO()
                            writer = csv.writer(output)
                            writer.writerow(['attempt_id','quiz_title','user_email','score','max_score','finished_at'])
                            for a in attempts:
                                writer.writerow([a['attempt_id'], a['quiz_title'], a['user_email'], a['score'], a['max_score'], a['finished_at']])
                            st.download_button("CSV İndir (Filtreli)", data=output.getvalue(), file_name=f"attempts_class_{active_class.code}_filtered.csv", mime="text/csv")

                        for a in attempts:
                            with st.expander(f"{a['finished_at'] or ''} | {a['user_email']} | {a['quiz_title']} | {a['score']}/{a['max_score']}"):
                                st.write(f"Attempt ID: {a['attempt_id']}")
                                det = get_attempt_detail(a['attempt_id'])
                                if det:
                                    for pq in det['per_question']:
                                        st.write(f"- ({'Doğru' if pq['correct'] else 'Yanlış'}) {pq['question_text']} [{pq['points']}]")
                    else:
                        st.info("Henüz deneme yok.")

                # For students: list published quizzes and allow attempt
                st.markdown("---")
                st.subheader("Sınıftaki Yayınlanmış Quizler")
                quizzes = get_quizzes_for_class(active_class.id)
                pub_quizzes = [q for q in quizzes if q.published]
                if pub_quizzes:
                    for pq in pub_quizzes:
                        with st.expander(f"{pq.title} — Yayınlandı"):
                            st.write(f"Oluşturan: {pq.author_id} — Oluşturuldu: {pq.created_at}")
                            if st.session_state.user.get('role') == 'student':
                                if st.button("Quiz'e Katıl", key=f"att_{pq.id}"):
                                    # load questions into session
                                    qs = get_questions_for_quiz(pq.id)
                                    st.session_state.current_attempt = {'quiz_id': pq.id, 'questions': [{ 'id': q.id, 'type': q.type, 'text': q.text, 'choices': json.loads(q.choices) if q.choices else None } for q in qs]}
                                    st.experimental_rerun()
                else:
                    st.info("Henüz yayınlanmış bir quiz yok.")

                # If there is a current attempt in session, show attempt UI
                if st.session_state.get('current_attempt'):
                    attempt = st.session_state.current_attempt
                    st.markdown('---')
                    st.subheader('Quiz Denemesi')
                    answers = []
                    for q in attempt['questions']:
                        st.write(f"**{q['text']}**")
                        if q['type'] == 'mcq':
                            opt = st.radio(f"Secim {q['id']}", options=list(q['choices'].keys()), key=f"ans_{q['id']}")
                            answers.append({'question_id': q['id'], 'answer': opt})
                        elif q['type'] == 'true_false':
                            val = st.selectbox(f"Doğru/Yanlış {q['id']}", options=['True','False'], key=f"ans_{q['id']}")
                            answers.append({'question_id': q['id'], 'answer': val})
                        elif q['type'] == 'fill_blank':
                            val = st.text_input(f"Cevap {q['id']}", key=f"ans_{q['id']}")
                            answers.append({'question_id': q['id'], 'answer': val})
                        else:
                            val = st.text_area(f"Cevap {q['id']}", key=f"ans_{q['id']}")
                            answers.append({'question_id': q['id'], 'answer': val})

                    if st.button('📝 Denemeyi Bitir'):
                        # gather answers from session state
                        gathered = []
                        for q in attempt['questions']:
                            a = st.session_state.get(f"ans_{q['id']}")
                            gathered.append({'question_id': q['id'], 'answer': a})
                        try:
                            res = grade_attempt(attempt['quiz_id'], st.session_state.user['id'], gathered)
                            st.success(f"Puan: {res['score']} / {res['max_score']}")
                            for pqres in res['per_question']:
                                st.write(f"Soru {pqres['question_id']}: {'Doğru' if pqres['correct'] else 'Yanlış'}")
                            st.session_state.current_attempt = None
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Hata: {e}")

            else:
                st.info("Henüz hiçbir sınıfa katılmadınız veya oluşturmadınız.")

    # Dosya Yükle
    if menu_option == "📤 Dosya Yükle":
        st.header("📤 Ders Notu Yükleme")
        st.write("PDF, DOCX veya TXT formatında ders notlarınızı yükleyin.")
        
        uploaded_file = st.file_uploader(
            "Dosya seçin",
            type=['pdf', 'docx', 'txt'],
            help="Desteklenen formatlar: PDF, DOCX, TXT"
        )
        
        if uploaded_file is not None:
            st.info(f"📄 Seçilen dosya: {uploaded_file.name}")
            
            if st.button("🚀 Dosyayı İşle ve Kaydet", type="primary"):
                with st.spinner("Dosya işleniyor..."):
                    try:
                        # Dosyayı işle
                        documents = st.session_state.rag_processor.process_document(
                            uploaded_file, 
                            uploaded_file.name
                        )
                        
                        # Vektör veritabanına ekle
                        st.session_state.rag_processor.add_documents_to_vectorstore(documents)
                        
                        st.success(f"✅ {uploaded_file.name} başarıyla yüklendi ve işlendi!")
                        st.success(f"📊 {len(documents)} metin parçası oluşturuldu")
                        
                        # Dosya listesini güncelle
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
    
    # Soru-Cevap
    elif menu_option == "💬 Soru-Cevap":
        st.header("💬 Ders Notları Hakkında Soru Sorun")
        
        sources = st.session_state.rag_processor.get_all_sources()
        if not sources:
            st.warning("⚠️ Henüz dosya yüklenmedi. Lütfen önce dosya yükleyin.")
        else:
            st.info("📚 Yüklediğiniz ders notları hakkında soru sorabilirsiniz.")
            
            # Chat geçmişini göster
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            
            # Kullanıcı sorusu
            user_question = st.chat_input("Sorunuzu yazın...")
            
            if user_question:
                # Kullanıcı mesajını göster
                with st.chat_message("user"):
                    st.write(user_question)
                
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_question
                })
                
                # İlgili dokümanları bul
                with st.spinner("Cevap hazırlanıyor..."):
                    relevant_docs = st.session_state.rag_processor.search_documents(
                        user_question, 
                        k=4
                    )
                    
                    # Groq ile cevap oluştur
                    if relevant_docs and len(relevant_docs) > 0:
                        answer = st.session_state.groq_client.answer_question(
                            user_question,
                            relevant_docs
                        )
                    else:
                        answer = "Üzgünüm, bu konuda ders notlarınızda ilgili bilgi bulamadım. Lütfen farklı bir soru sormayı deneyin veya daha fazla ders notu yükleyin."
                
                # Asistan cevabını göster
                with st.chat_message("assistant"):
                    st.write(answer)
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })
            
            # Chat geçmişini temizle butonu
            if st.session_state.chat_history:
                if st.button("🗑️ Chat Geçmişini Temizle"):
                    st.session_state.chat_history = []
                    st.rerun()
    
    # Özet Oluştur
    elif menu_option == "📝 Özet Oluştur":
        st.header("📝 Ders Notu Özetleme")
        
        sources = st.session_state.rag_processor.get_all_sources()
        if not sources:
            st.warning("⚠️ Henüz dosya yüklenmedi. Lütfen önce dosya yükleyin.")
        else:
            st.write("Yüklediğiniz ders notlarından özet oluşturun.")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                summary_topic = st.text_input(
                    "Özet konusu (opsiyonel)",
                    placeholder="Örn: Python programlama temelleri"
                )
            
            with col2:
                detail_level = st.selectbox(
                    "Özet detay seviyesi",
                    ["kısa", "orta", "detaylı"],
                    index=1
                )
            
            if st.button("📄 Özet Oluştur", type="primary"):
                with st.spinner("Özet oluşturuluyor..."):
                    try:
                        # İlgili dokümanları bul
                        if summary_topic:
                            docs = st.session_state.rag_processor.search_documents(
                                summary_topic,
                                k=6
                            )
                        else:
                            # Tüm dokümanlardan örnek al
                            docs = st.session_state.rag_processor.search_documents("genel bilgi", k=6)
                        
                        if docs and len(docs) > 0:
                            # Bağlamı oluştur
                            context = "\n\n".join([doc.page_content for doc in docs])
                            
                            # Özet oluştur
                            summary = st.session_state.groq_client.generate_summary(
                                context,
                                detail_level
                            )
                            
                            st.success("✅ Özet başarıyla oluşturuldu!")
                            st.markdown("---")
                            st.markdown("### 📋 Özet:")
                            st.markdown(summary)
                            
                        else:
                            st.error("İlgili içerik bulunamadı.")
                            
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
    
    # Quiz Oluştur
    elif menu_option == "🎯 Quiz Oluştur":
        st.header("🎯 Quiz Oluşturma")
        
        sources = st.session_state.rag_processor.get_all_sources()
        if not sources:
            st.warning("⚠️ Henüz dosya yüklenmedi. Lütfen önce dosya yükleyin.")
        else:
            st.write("Ders notlarınızdan otomatik quiz soruları oluşturun.")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                quiz_topic = st.text_input(
                    "Quiz konusu (opsiyonel)",
                    placeholder="Örn: Veri yapıları"
                )
            
            with col2:
                num_questions = st.number_input(
                    "Soru sayısı",
                    min_value=1,
                    max_value=10,
                    value=5
                )
            
            col3, col4 = st.columns(2)
            
            with col3:
                quiz_type = st.selectbox(
                    "Quiz Türü",
                    ["Çoktan Seçmeli", "Doğru/Yanlış", "Boşluk Doldurma", "Kısa Cevap"],
                    index=0
                )
            
            with col4:
                difficulty = st.selectbox(
                    "Zorluk Seviyesi",
                    ["Kolay", "Orta", "Zor"],
                    index=1
                )
            
            if st.button("🎲 Quiz Oluştur", type="primary"):
                with st.spinner("Quiz oluşturuluyor..."):
                    try:
                        # İlgili dokümanları bul
                        if quiz_topic:
                            docs = st.session_state.rag_processor.search_documents(
                                quiz_topic,
                                k=6
                            )
                        else:
                            docs = st.session_state.rag_processor.search_documents("genel bilgi", k=6)
                        
                        if docs and len(docs) > 0:
                            # Bağlamı oluştur
                            context = "\n\n".join([doc.page_content for doc in docs])
                            
                            # Quiz türünü ve zorluk seviyesini belirle
                            quiz_type_map = {
                                "Çoktan Seçmeli": "multiple_choice",
                                "Doğru/Yanlış": "true_false",
                                "Boşluk Doldurma": "fill_blank",
                                "Kısa Cevap": "short_answer"
                            }
                            
                            difficulty_map = {
                                "Kolay": "kolay",
                                "Orta": "orta",
                                "Zor": "zor"
                            }
                            
                            # Quiz oluştur
                            st.session_state.quiz_questions = st.session_state.groq_client.generate_quiz(
                                context,
                                num_questions,
                                quiz_type_map[quiz_type],
                                difficulty_map[difficulty]
                            )
                            
                            if st.session_state.quiz_questions and 'error' not in st.session_state.quiz_questions[0]:
                                st.success(f"✅ {len(st.session_state.quiz_questions)} soru başarıyla oluşturuldu!")
                                st.rerun()
                            else:
                                st.error("Quiz oluşturulamadı.")
                                
                        else:
                            st.error("İlgili içerik bulunamadı.")
                            
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
            
            # Soruları göster
            if st.session_state.quiz_questions:
                st.markdown("---")
                for i, q in enumerate(st.session_state.quiz_questions, 1):
                    q_type = q.get('type', 'multiple_choice')
                    
                    if q_type == 'multiple_choice' or ('question' in q and 'A' in q):
                        # Çoktan seçmeli
                        with st.expander(f"📝 Soru {i}: {q.get('question', 'Soru bulunamadı')}", expanded=True):
                            st.write(f"**A)** {q.get('A', '')}")
                            st.write(f"**B)** {q.get('B', '')}")
                            st.write(f"**C)** {q.get('C', '')}")
                            st.write(f"**D)** {q.get('D', '')}")
                            
                            if st.button(f"Doğru Cevabı Göster", key=f"answer_{i}"):
                                st.success(f"✅ Doğru Cevap: **{q.get('correct_answer', 'A')}**")
                                if 'explanation' in q:
                                    st.info(f"💡 {q['explanation']}")
                    
                    elif q_type == 'true_false':
                        # Doğru/Yanlış
                        with st.expander(f"✓/✗ Soru {i}: {q.get('statement', 'İfade bulunamadı')}", expanded=True):
                            if st.button(f"Doğru Cevabı Göster", key=f"answer_{i}"):
                                st.success(f"✅ Doğru Cevap: **{q.get('correct_answer', 'Doğru')}**")
                                if 'explanation' in q:
                                    st.info(f"💡 {q['explanation']}")
                    
                    elif q_type == 'fill_blank':
                        # Boşluk doldurma
                        with st.expander(f"__ Soru {i}: Boşluğu doldurun", expanded=True):
                            st.write(q.get('sentence', 'Cümle bulunamadı'))
                            
                            if st.button(f"Doğru Cevabı Göster", key=f"answer_{i}"):
                                st.success(f"✅ Doğru Cevap: **{q.get('correct_answer', '')}**")
                                if 'explanation' in q:
                                    st.info(f"💡 {q['explanation']}")
                    
                    elif q_type == 'short_answer':
                        # Kısa cevap
                        with st.expander(f"✍️ Soru {i}: {q.get('question', 'Soru bulunamadı')}", expanded=True):
                            if st.button(f"Örnek Cevabı Göster", key=f"answer_{i}"):
                                st.success(f"✅ Örnek Cevap: **{q.get('sample_answer', '')}**")
                                if 'keywords' in q and q['keywords']:
                                    st.info(f"🔑 Anahtar Kelimeler: {', '.join(q['keywords'])}")
                
                if st.button("🗑️ Quizi Temizle"):
                    st.session_state.quiz_questions = []
                    st.rerun()
    
    # Yönetim
    elif menu_option == "📊 Yönetim":
        st.header("📊 Sistem Yönetimi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📁 Veritabanı Bilgileri")
            sources = st.session_state.rag_processor.get_all_sources()
            st.metric("Yüklenmiş Dosya Sayısı", len(sources))
            
            if sources:
                st.write("**Dosyalar:**")
                for i, source in enumerate(sources, 1):
                    st.write(f"{i}. {source}")
        
        with col2:
            st.subheader("🗑️ Tehlikeli İşlemler")
            st.warning("⚠️ Bu işlemler geri alınamaz!")
            
            if st.button("🗑️ Tüm Veritabanını Temizle", type="secondary"):
                if st.session_state.rag_processor.delete_collection():
                    st.success("✅ Veritabanı temizlendi!")
                    st.session_state.chat_history = []
                    st.rerun()
                else:
                    st.error("❌ Veritabanı temizlenemedi.")
        
        st.divider()
        
        st.subheader("ℹ️ Sistem Bilgileri")
        st.info("""
        **Akıllı Ders Asistanı v1.0**
        
        - 🔹 **Yerel Vektör DB:** ChromaDB
        - 🔹 **Cloud LLM:** Groq API (Llama 3.3 70B)
        - 🔹 **Embedding Model:** all-MiniLM-L6-v2
        - 🔹 **Desteklenen Formatlar:** PDF, DOCX, TXT
        
        **Özellikler:**
        - RAG tabanlı doküman işleme
        - Akıllı soru-cevap sistemi
        - Otomatik özet oluşturma
        - Quiz ve test oluşturma
        """)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>Akıllı Ders Asistanı - RAG Destekli Öğrenme Sistemi</small>
    </div>
""", unsafe_allow_html=True)
