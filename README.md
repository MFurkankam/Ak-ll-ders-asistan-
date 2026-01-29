# Akıllı Ders Asistanı

Ders notlarını **yükleyip**, içeriklerine dayalı **soru-cevap**, **özet**, **quiz üretimi** ve **sınıf yönetimi** sunan çok sayfalı bir **Streamlit** uygulaması. Notlardan güvenilir yanıtlar üretmek için **RAG (Retrieval Augmented Generation)** yaklaşımını kullanır ve sonuçları analiz eden **raporlar** içerir.

---

## Özellikler

- **Not Yükleme ve Kütüphane** (PDF/DOCX/TXT)
- **Notlara Dayalı Soru-Cevap (RAG + LLM)**
- **Özetleme** (kısa / orta / detaylı / çok detaylı)
- **Quiz Üretimi** (Çoktan Seçmeli, Doğru-Yanlış, Boşluk Doldurma, Kısa Cevap)
- **Sınıf Yönetimi** (oluşturma, katılma, güncelleme, silme)
- **Quiz Yayınlama ve Deneme Limitleri**
- **Raporlar** (konu başarısı, öğrenci segmenti, zaman trendi)

---

## Teknoloji Yığını

- **Python**, **Streamlit** (çok sayfalı arayüz)
- **Groq API + LangChain** (LLM entegrasyonu)
- **ChromaDB** (vektör veritabanı / RAG)
- **PostgreSQL + SQLModel/SQLAlchemy** (kalıcı veri)
- **Alembic** (migrasyon)
- **Pandas + Altair** (raporlar ve grafikler)
- **pytest** (testler)

---

## Hızlı Başlangıç (Local)

### 1) Bağımlılıklar

```bash
python -m pip install -r requirements.txt
```

### 2) Postgres (Docker ile önerilir)

```bash
docker compose up -d db
```

> Not: Postgres varsayılan olarak **5433** portunda çalışır.

### 3) Ortam Değişkenleri

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="YOUR_GROQ_KEY"
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
```

**macOS / Linux:**
```bash
export GROQ_API_KEY="YOUR_GROQ_KEY"
export DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
```

### 4) Migrasyonları Çalıştır

```bash
python -m alembic upgrade head
```

### 5) Uygulamayı Başlat

```bash
python -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

Tarayıcıdan: **http://localhost:5000**

---

## Docker (Uygulama + Postgres)

```bash
docker compose up --build
```

---

## Ortam Değişkenleri

| Değişken | Açıklama | Örnek |
|---|---|---|
| `GROQ_API_KEY` | Groq API anahtarı | `gsk_...` |
| `DATABASE_URL` | PostgreSQL bağlantı URL’i | `postgresql+psycopg2://...` |
| `RAG_CHUNK_SIZE` | RAG parça boyutu | `1000` |
| `RAG_CHUNK_OVERLAP` | RAG parça overlap | `200` |

---

## Testler

### SQLite ile (önerilir, hızlı ve izole)
```bash
$env:DATABASE_URL="sqlite:///./test.db"
python scripts\run_tests_direct.py
```

### PostgreSQL ile
```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\run_tests_direct.py
```

> Not: PostgreSQL üzerinde testler kalıcı veri bırakır. Aynı testleri tekrar çalıştırırken sınıf kodu çakışması olabilir. SQLite bu yüzden tavsiye edilir.

---

## Raporlar için Seed (Sahte Veri)

Var olan sınıfa raporları test etmek için sahte veri ekleyebilirsiniz:

```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\seed_reports.py --class-code 1RMMI1 --students 12 --quizzes 3 --topics 5 --questions 6
```

Temizlemek için:

```bash
python scripts\seed_reports_cleanup.py --class-code 1RMMI1
```

---

## Proje Yapısı

```
.
├─ app.py
├─ pages/
│  ├─ 1_Dosya_Yukle.py
│  ├─ 2_Soru_Cevap.py
│  ├─ 3_Ozet.py
│  ├─ 4_Quiz.py
│  ├─ 5_Siniflar.py
│  └─ ...
├─ utils/
│  ├─ groq_client.py
│  ├─ rag_processor.py
│  ├─ quiz.py
│  ├─ db.py
│  ├─ models.py
│  └─ ...
├─ scripts/
│  ├─ run_tests_direct.py
│  ├─ seed_reports.py
│  └─ seed_reports_cleanup.py
├─ tests/
└─ alembic/
```

---

## Sık Karşılaşılan Sorunlar

**1) “streamlit komutu bulunamadı”**
- `python -m streamlit ...` şeklinde çalıştırın.

**2) Postgres 5432’ye bağlanıyor**
- `DATABASE_URL`’i **5433** portu ile ayarlayın.

**3) Groq API key hatası**
- `GROQ_API_KEY` ortam değişkenini kontrol edin.

**4) Raporlarda ısı haritası hatası**
- `matplotlib` yüklü olmalı: `python -m pip install matplotlib`

---

## Güvenlik Notları

- API anahtarlarını **kod içine yazmayın**, env var kullanın.
- Yüklenen notlar kullanıcı verisidir; erişim ve saklama politikası önemlidir.

---

## Lisans

Şu an lisans belirtilmemiştir. (İsterseniz MIT / Apache-2.0 vb. ekleyebiliriz.)

---

## Katkı

PR ve Issue’lar memnuniyetle kabul edilir. Büyük değişiklikler öncesi konu açılması önerilir.
