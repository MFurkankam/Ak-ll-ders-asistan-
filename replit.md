# Akıllı Ders Asistanı - RAG Destekli Öğrenme Sistemi

## Proje Genel Bakış
Türkçe dil desteği ile RAG (Retrieval-Augmented Generation) tabanlı akıllı ders asistanı uygulaması. Öğrencilerin ders notlarını yükleyip, özetler oluşturabilecekleri, quiz çözebilecekleri ve soru-cevap yapabilecekleri bir sistem.

## Sistem Mimarisi

### Hibrit RAG Sistemi
- **Yerel Vektör Veritabanı:** ChromaDB - Dokümanların yerel olarak saklanması ve aranması
- **Cloud LLM:** Groq API - Llama 3.3 70B Versatile model ile metin üretimi
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (CPU optimized)

## Özellikler

### 1. Dosya Yükleme ve İşleme
- PDF, DOCX, TXT formatlarında dosya desteği
- Otomatik metin çıkarma ve parçalama (chunking)
- ChromaDB vektör veritabanına kaydetme
- Embedding oluşturma ve indeksleme

### 2. Akıllı Soru-Cevap Sistemi
- RAG tabanlı doküman arama
- Bağlam farkındalıklı cevap üretimi
- Chat geçmişi yönetimi
- Türkçe dil desteği

### 3. Ders Notu Özetleme
- Üç farklı detay seviyesi (kısa, orta, detaylı)
- Konu bazlı özet oluşturma
- LLM destekli akıllı özetleme

### 4. Quiz Oluşturma
- **Çoklu Format Desteği:**
  - Çoktan seçmeli (4 seçenek)
  - Doğru/Yanlış
  - Boşluk doldurma
  - Kısa cevaplı sorular
- **Zorluk Seviyeleri:**
  - Kolay (temel kavramlar)
  - Orta (uygulama gerektiren)
  - Zor (analiz ve sentez)
- Özelleştirilebilir soru sayısı (1-10)
- Doğru cevap ve açıklama içerir
- Konu bazlı quiz oluşturma

### 5. Flashcard Oluşturma
- Otomatik çalışma kartı üretimi
- Ön yüz (soru/kavram) ve arka yüz (cevap/açıklama)
- Özelleştirilebilir kart sayısı (5-20)
- Konu bazlı flashcard oluşturma
- İnteraktif göster/gizle özelliği

### 6. Sistem Yönetimi
- Yüklenmiş dosyaları görüntüleme
- Veritabanı istatistikleri
- Veritabanı temizleme

## Teknik Detaylar

### Dosya Yapısı
```
/
├── app.py                      # Ana Streamlit uygulaması
├── utils/
│   ├── __init__.py
│   ├── rag_processor.py       # RAG işleme ve ChromaDB yönetimi
│   └── groq_client.py         # Groq API entegrasyonu
├── chroma_db/                 # ChromaDB vektör veritabanı (runtime)
└── .streamlit/
    └── config.toml            # Streamlit yapılandırması
```

### Kullanılan Teknolojiler
- **Framework:** Streamlit
- **Vektör DB:** ChromaDB 1.3.5
- **LLM Framework:** LangChain
- **LLM Provider:** Groq API (Llama 3.3 70B)
- **Embeddings:** HuggingFace Transformers
- **Doküman İşleme:** PyPDF2, python-docx

### Environment Variables
- `GROQ_API_KEY`: Groq API anahtarı (gerekli)

## Kullanım Akışı

1. **API Key Ayarlama:** Sidebar'dan Groq API key'i girin
2. **Dosya Yükleme:** PDF, DOCX veya TXT dosyalarını yükleyin
3. **İşlem Seçimi:** 
   - Soru-cevap için chat bölümünü kullanın
   - Özet oluşturmak için özet sekmesini açın
   - Quiz oluşturmak için quiz bölümüne gidin
4. **Yönetim:** Yüklenen dosyaları görüntüleyin veya veritabanını temizleyin

## RAG Pipeline Detayları

### 1. Doküman İşleme
- Dosya yükleme ve format tespiti
- Metin çıkarma (PDF/DOCX/TXT)
- RecursiveCharacterTextSplitter ile parçalama
  - Chunk size: 1000 karakter
  - Chunk overlap: 200 karakter

### 2. Vektör Oluşturma
- HuggingFace all-MiniLM-L6-v2 model
- 384 boyutlu vektörler
- ChromaDB'de saklama

### 3. Retrieval
- Similarity search (k=4 varsayılan)
- Bağlam oluşturma
- LLM'e gönderme

### 4. Generation
- Groq Llama 3.3 70B model
- Temperature: 0.7
- Max tokens: 2048
- Türkçe prompt'lar

## Güvenlik ve Performans
- API anahtarları session state'de güvenli saklanır
- Yerel vektör veritabanı - veri gizliliği
- CPU optimized embeddings
- Asenkron işleme desteği

## Son Güncellemeler
- **22 Kasım 2024:** İlk versiyon tamamlandı
  - Tüm temel özellikler implement edildi
  - ChromaDB + Groq API entegrasyonu yapıldı
  - Türkçe UI ve prompt desteği eklendi
