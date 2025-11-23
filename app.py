import streamlit as st
import os
from utils.rag_processor import RAGProcessor
from utils.groq_client import GroqClient

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

# Session state başlatma
if 'rag_processor' not in st.session_state:
    st.session_state.rag_processor = RAGProcessor()

if 'groq_client' not in st.session_state:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        st.session_state.groq_client = GroqClient(groq_api_key)
    else:
        st.session_state.groq_client = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

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
        ["📤 Dosya Yükle", "💬 Soru-Cevap", "📝 Özet Oluştur", "🎯 Quiz Oluştur", "📊 Yönetim"],
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
                            questions = st.session_state.groq_client.generate_quiz(
                                context,
                                num_questions,
                                quiz_type_map[quiz_type],
                                difficulty_map[difficulty]
                            )
                            
                            if questions and 'error' not in questions[0]:
                                st.success(f"✅ {len(questions)} soru başarıyla oluşturuldu!")
                                st.markdown("---")
                                
                                # Soruları göster
                                for i, q in enumerate(questions, 1):
                                    q_type = q.get('type', 'multiple_choice')
                                    
                                    if q_type == 'multiple_choice' or 'question' in q and 'A' in q:
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
                            else:
                                st.error("Quiz oluşturulamadı.")
                                
                        else:
                            st.error("İlgili içerik bulunamadı.")
                            
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
    
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
