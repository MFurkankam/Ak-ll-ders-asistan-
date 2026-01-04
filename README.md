# Akilli Ders Asistani

## Local (Streamlit + Postgres)

1) Start Postgres (Docker):
```bash
docker compose up -d db
```

2) Install deps:
```bash
python -m pip install -r requirements.txt
```

3) Run Streamlit:
```bash
set DATABASE_URL=postgresql+psycopg2://akilli:akilli_pass@localhost:5432/akilli_db
python -m streamlit run app.py
```

## Docker (App + Postgres)

```bash
docker compose up --build
```
