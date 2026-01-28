# Ak�ll� Ders Asistan�

Ders notlar�n� **y�kleyip**, onlar�n i�eri�ine dayal� **soru-cevap**, **�zet**, **quiz �retimi** ve **s�n�f y�netimi** sunan �ok sayfal� bir **Streamlit** uygulamas�. Notlar�n�zdan g�venilir yan�tlar �retmek i�in **RAG (Retrieval Augmented Generation)** yakla��m�n� kullan�r ve sonu�lar� analiz eden **raporlar** i�erir.

---

## �zellikler

- **Not Y�kleme ve K�t�phane** (PDF/DOCX/TXT)
- **Notlara Dayal� Soru-Cevap (RAG + LLM)**
- **�zetleme** (k�sa / orta / detayl� / �ok detayl�)
- **Quiz �retimi** (�oktan Se�meli, Do�ru-Yanl��, Bo�luk Doldurma, K�sa Cevap)
- **S�n�f Y�netimi** (olu�turma, kat�lma, g�ncelleme, silme)
- **Quiz Yay�nlama ve Deneme Limitleri**
- **Raporlar** (konu ba�ar�s�, ��renci segmenti, zaman trendi)

---

## Teknoloji Y���n�

- **Python**, **Streamlit** (�ok sayfal� aray�z)
- **Groq API + LangChain** (LLM entegrasyonu)
- **ChromaDB** (vekt�r veritaban� / RAG)
- **PostgreSQL + SQLModel/SQLAlchemy** (kal�c� veri)
- **Alembic** (migrasyon)
- **Pandas + Altair** (raporlar ve grafikler)
- **pytest** (testler)

---

## H�zl� Ba�lang�� (Local)

### 1) Ba��ml�l�klar

```bash
python -m pip install -r requirements.txt
```

### 2) Postgres (Docker ile �nerilir)

```bash
docker compose up -d db
```

> Not: Postgres varsay�lan olarak **5433** portunda �al���r.

### 3) Ortam De�i�kenleri

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

### 4) Migrasyonlar� �al��t�r

```bash
python -m alembic upgrade head
```

### 5) Uygulamay� Ba�lat

```bash
python -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0
```

Taray�c�dan: **http://localhost:5000**

---

## Docker (Uygulama + Postgres)

```bash
docker compose up --build
```

---

## Ortam De�i�kenleri

| De�i�ken | A��klama | �rnek |
|---|---|---|
| `GROQ_API_KEY` | Groq API anahtar� | `gsk_...` |
| `DATABASE_URL` | PostgreSQL ba�lant� URL�i | `postgresql+psycopg2://...` |
| `RAG_CHUNK_SIZE` | RAG par�a boyutu | `1000` |
| `RAG_CHUNK_OVERLAP` | RAG par�a overlap | `200` |

---

## Testler

### SQLite ile (�nerilir, h�zl� ve izole)
```bash
$env:DATABASE_URL="sqlite:///./test.db"
python scripts\run_tests_direct.py
```

### PostgreSQL ile
```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\run_tests_direct.py
```

> Not: PostgreSQL �zerinde testler kal�c� veri b�rak�r. Ayn� testleri tekrar �al��t�r�rken s�n�f kodu �ak��mas� olabilir. SQLite bu y�zden tavsiye edilir.

---

## Raporlar i�in Seed (Sahte Veri)

Var olan s�n�fa raporlar� test etmek i�in sahte veri ekleyebilirsiniz:

```bash
$env:DATABASE_URL="postgresql+psycopg2://akilli:akilli_pass@localhost:5433/akilli_db"
python scripts\seed_reports.py --class-code 1RMMI1 --students 12 --quizzes 3 --topics 5 --questions 6
```

Temizlemek i�in:

```bash
python scripts\seed_reports_cleanup.py --class-code 1RMMI1
```

---

## Proje Yap�s�

```
.
+� app.py
+� pages/
-  +� 1_Dosya_Yukle.py
-  +� 2_Soru_Cevap.py
-  +� 3_Ozet.py
-  +� 4_Quiz.py
-  +� 5_Siniflar.py
-  L� ...
+� utils/
-  +� groq_client.py
-  +� rag_processor.py
-  +� quiz.py
-  +� db.py
-  +� models.py
-  L� ...
+� scripts/
-  +� run_tests_direct.py
-  +� seed_reports.py
-  L� seed_reports_cleanup.py
+� tests/
L� alembic/
```

---

## G�venlik Notlar�

- Y�klenen notlar kullan�c� verisidir; eri�im ve saklama politikas� �nemlidir.

---

## Lisans

�u an lisans belirtilmemi�tir. (�sterseniz MIT / Apache-2.0 vb. ekleyebiliriz.)

---

## Katk�

PR ve Issue�lar memnuniyetle kabul edilir. B�y�k de�i�iklikler �ncesi konu a��lmas� �nerilir.
