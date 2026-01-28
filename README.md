# Akýllý Ders Asistaný

Ders notlarýný **yükleyip**, onlarýn içeriðine dayalý **soru-cevap**, **özet**, **quiz üretimi** ve **sýnýf yönetimi** sunan çok sayfalý bir **Streamlit** uygulamasý. Notlarýnýzdan güvenilir yanýtlar üretmek için **RAG (Retrieval Augmented Generation)** yaklaþýmýný kullanýr ve sonuçlarý analiz eden **raporlar** içerir.

---

## Özellikler

- **Not Yükleme ve Kütüphane** (PDF/DOCX/TXT)
- **Notlara Dayalý Soru-Cevap (RAG + LLM)**
- **Özetleme** (kýsa / orta / detaylý / çok detaylý)
- **Quiz Üretimi** (Çoktan Seçmeli, Doðru-Yanlýþ, Boþluk Doldurma, Kýsa Cevap)
- **Sýnýf Yönetimi** (oluþturma, katýlma, güncelleme, silme)
- **Quiz Yayýnlama ve Deneme Limitleri**
- **Raporlar** (konu baþarýsý, öðrenci segmenti, zaman trendi)

---

## Teknoloji Yýðýný

- **Python**, **Streamlit** (çok sayfalý arayüz)
- **Groq API + LangChain** (LLM entegrasyonu)
- **ChromaDB** (vektör veritabaný / RAG)
- **PostgreSQL + SQLModel/SQLAlchemy** (kalýcý veri)
- **Alembic** (migrasyon)
- **Pandas + Altair** (raporlar ve grafikler)
- **pytest** (testler)

---

## Hýzlý Baþlangýç (Local)

### 1) Baðýmlýlýklar

```bash
python -m pip install -r requirements.txt
```

### 2) Postgres (Docker ile önerilir)

```bash
docker compose up -d db
```

> Not: Postgres varsayýlan olarak **5433** portunda çalýþýr.

### 3) Ortam Deðiþkenleri

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

### 4) Migrasyonlarý Çalýþtýr

```bash
python -m alembic upgrade head
```

### 5) Uygulamayý Baþlat

```bash
python -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

Tarayýcýdan: **http://localhost:5000**

---

## Docker (Uygulama + Postgres)

```bash
docker compose up --build
```

---

## Ortam Deðiþkenleri

| Deðiþken | Açýklama | Örnek |
|---|---|---|
| `GROQ_API_KEY` | Groq API anahtarý | `gsk_...` |
| `DATABASE_URL` | PostgreSQL baðlantý URL’i | `postgresql+psycopg2://...` |
| `RAG_CHUNK_SIZE` | RAG parça boyutu | `1000` |
| `RAG_CHUNK_OVERLAP` | RAG parça overlap | `200` |

---

## Testler

### SQLite ile (önerilir, hýzlý ve izole)
```bash
$env:DATABASE_URL="sqlite:///./test.db"
python scripts\run_tests_direct.py
```

### PostgreSQL 5433 ile
```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\run_tests_direct.py
```

> Not: PostgreSQL üzerinde testler kalýcý veri býrakýr. Ayný testleri tekrar çalýþtýrýrken sýnýf kodu çakýþmasý olabilir. SQLite bu yüzden tavsiye edilir.

---

## Raporlar için Seed (Sahte Veri)

Var olan sýnýfa raporlarý test etmek için sahte veri ekleyebilirsiniz:

```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\seed_reports.py --class-code 1RMMI1 --students 12 --quizzes 3 --topics 5 --questions 6
```

Temizlemek için:

```bash
python scripts\seed_reports_cleanup.py --class-code 1RMMI1
```

---

## Proje Yapýsý

```
.
+¦ app.py
+¦ pages/
-  +¦ 1_Dosya_Yukle.py
-  +¦ 2_Soru_Cevap.py
-  +¦ 3_Ozet.py
-  +¦ 4_Quiz.py
-  +¦ 5_Siniflar.py
-  L¦ ...
+¦ utils/
-  +¦ groq_client.py
-  +¦ rag_processor.py
-  +¦ quiz.py
-  +¦ db.py
-  +¦ models.py
-  L¦ ...
+¦ scripts/
-  +¦ run_tests_direct.py
-  +¦ seed_reports.py
-  L¦ seed_reports_cleanup.py
+¦ tests/
L¦ alembic/
```

---

## Sýk Karþýlaþýlan Sorunlar

**1) “streamlit komutu bulunamadý”**
- `python -m streamlit ...` þeklinde çalýþtýrýn.

**2) Postgres 5432’ye baðlanýyor**
- `DATABASE_URL`’i **5433** portu ile ayarlayýn.

**3) Groq API key hatasý**
- `GROQ_API_KEY` ortam deðiþkenini kontrol edin.

**4) Raporlarda ýsý haritasý hatasý**
- `matplotlib` yüklü olmalý: `python -m pip install matplotlib`

---

## Güvenlik Notlarý

- API anahtarlarýný **kod içine yazmayýn**, env var kullanýn.
- Yüklenen notlar kullanýcý verisidir; eriþim ve saklama politikasý önemlidir.

---

## Lisans

Þu an lisans belirtilmemiþtir. (Ýsterseniz MIT / Apache-2.0 vb. ekleyebiliriz.)

---

## Katký

PR ve Issue’lar memnuniyetle kabul edilir. Büyük deðiþiklikler öncesi konu açýlmasý önerilir.
