# 🔍 AI Log Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb.svg)](https://react.dev/)

**AI Log Analyzer** è un prodotto SaaS multi-utente che sfrutta i modelli AI più avanzati
(**Google Gemini**, **OpenAI** e **Anthropic Claude**, a scelta) per assistere SRE, DevOps,
sviluppatori e QA Engineer nell'analisi dei log applicativi e infrastrutturali.

Ogni utente ha un proprio account, un piano con quota mensile di analisi e uno storico
persistente dei report generati. Il tool automatizza l'estrazione delle anomalie, categorizza
i messaggi di errore per gravità, stima in tempo reale i costi di utilizzo delle API AI ed
elabora un report strutturato (Root Cause Analysis e raccomandazioni di fix) grazie agli
**Structured Output** nativi di ogni provider.

---

## 🚀 Caratteristiche Principali

* **Account utente & storico**: registrazione/login via JWT, ogni report generato resta
  salvato e consultabile dalla pagina Storico.
* **Multi-provider AI**: scegli tra **Google Gemini**, **OpenAI** e **Anthropic Claude** —
  è la piattaforma a fornire l'accesso all'AI (chiavi lato server), l'utente non deve portare
  una propria chiave API.
* **Piani a quota**: piano Free e Pro con limite di analisi mensili (nessun pagamento reale
  collegato in questa fase — vedi [Roadmap](#-roadmap--fuori-scope-in-questa-fase)).
* **Parsing Multiformato & Rilevamento Traceback**: parsing intelligente dei log con
  raggruppamento di stack trace complesse multi-riga (es. Java Spring Boot, Python Tracebacks).
* **Dashboard Statistica Interattiva**: ripartizione delle severità (`CRITICAL`, `ERROR`,
  `WARNING`, `INFO`, `DEBUG`) tramite grafico a ciambella e metriche riassuntive.
* **Evidenziatore Sintattico Server-Side**: syntax highlighting dei log calcolato lato backend
  (nessun rallentamento del browser su file grandi).
* **Pannello di Stima dei Costi in Tempo Reale**: calcolo preventivo dei costi input/output per
  ogni provider e modello, con suggerimento del modello più economico a parità di provider.
* **Filtri Avanzati**: severità multi-selezione, ricerca testuale/regex, selezione Prime/Ultime N
  righe, deduplicazione delle righe ripetute consecutive.
* **Hardening**: rate limiting sulle chiamate AI, limite dimensione upload, validazione
  centralizzata, nessuno stacktrace esposto al client, CORS ristretto.

---

## 🛠️ Tecnologie Utilizzate

**Backend** (`backend/`): Python 3.10+, FastAPI, SQLAlchemy 2.0 (SQLite in sviluppo), JWT
(`python-jose`), `bcrypt`, `slowapi` per il rate limiting.

**Logica di dominio** (`core/`): nessuna dipendenza da FastAPI — parsing log, formattazione,
astrazione multi-provider (`google-genai`, `openai`, `anthropic`), riusabile e testabile in
isolamento.

**Frontend** (`frontend/`): React 19 + Vite + TypeScript, Tailwind CSS, React Router, Recharts.

---

## 📋 Prerequisiti

* Python 3.10 o versione successiva.
* Node.js 20+ e npm.
* Almeno una API key tra: **Gemini API Key**, **OpenAI API Key**, **Anthropic API Key**
  (il provider senza chiave configurata non compare nel selettore del frontend).

---

## 💻 Installazione e Configurazione

### 1. Chiavi API e configurazione

```bash
cp .env.example .env
```

Apri `.env` e valorizza almeno una chiave provider (`GEMINI_API_KEY`, `OPENAI_API_KEY` o
`ANTHROPIC_API_KEY`) e un `JWT_SECRET` non banale.

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate  # Su Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn backend.app.main:app --reload
```

L'API è disponibile su **http://localhost:8000** (documentazione interattiva su `/docs`).

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

L'app è disponibile su **http://localhost:5173**.

### In alternativa: Docker Compose

```bash
docker compose up --build
```

Avvia backend (`:8000`) e frontend (`:5173`) insieme, leggendo le chiavi da `.env` in root.
Pensato per uso locale/sviluppo, non per deploy in produzione.

---

## 🧪 Test

```bash
pip install -r requirements-dev.txt
pytest
```

Esegue sia i test di `core/` (nessuna rete, nessuna chiave richiesta) sia quelli di
`backend/tests/` (DB SQLite temporaneo, provider AI sempre mockati).

---

## 📂 Struttura del Progetto

```
analyzer-ai/
├── core/                       # Logica pura, testata, senza FastAPI
│   ├── log_parser.py           #   parsing, filtri, dedupe, troncamento
│   ├── formatting.py           #   syntax highlighting, markdown→HTML, export .md
│   ├── report_schema.py        #   schema condiviso del report (Pydantic)
│   └── ai_providers/           #   astrazione multi-provider (Gemini/OpenAI/Anthropic)
├── config.py                   # Costanti condivise (severità, colori, provider, pricing)
├── backend/                    # API FastAPI (auth, quota, storico, orchestrazione)
│   ├── app/
│   │   ├── main.py, settings.py, db.py, models.py, schemas.py, auth.py, quota.py
│   │   └── routes/             #   auth, providers, logs, history, usage
│   └── tests/                  # Test pytest sull'API (DB temporaneo, provider mockati)
├── frontend/                   # React + Vite + TypeScript
│   └── src/
│       ├── pages/               #   Landing, Login, Register, Dashboard, History
│       ├── components/          #   card, filtri, grafici, selettore provider
│       └── lib/                 #   client API, auth context, markdown, tipi
├── tests/                      # Test pytest sulle funzioni pure di core/
├── AGENTS.md                   # Mappa del repo per agenti AI di coding
├── docker-compose.yml          # Ambiente locale backend+frontend
├── requirements.txt            # Dipendenze runtime (core/ + backend/)
├── sample_logs.log             # Log di esempio standard
├── complex_sample_logs.log     # Log di esempio complesso da 500 righe
├── LICENSE                     # Licenza MIT del progetto
└── README.md                   # Questa guida introduttiva
```

Per una mappa più dettagliata (cosa leggere per ogni tipo di modifica) vedi [AGENTS.md](AGENTS.md).

---

## 🗺️ Roadmap / fuori scope in questa fase

* **Pagamenti reali**: i piani Free/Pro esistono come modello dati e quota, ma non sono
  collegati a Stripe (o altro processore) — l'upgrade di piano è manuale.
* **Deploy cloud/CI-CD**: `docker-compose.yml` copre solo l'uso locale.
* **Migrazioni DB**: l'MVP crea lo schema con `create_all` su SQLite; da introdurre Alembic
  passando a Postgres in produzione.
* Le tariffe dei modelli OpenAI/Anthropic in `config.py` sono segnaposto indicativi da
  verificare contro le pricing page ufficiali prima di andare in produzione.

---

## 🧑‍💻 Autore

Ideato e sviluppato da:
* **Tommaso Ianniciello** - *Test Automation Engineer*
* **GitHub**: [@xtmms](https://github.com/xtmms)

---

## 📄 Licenza

Questo progetto è rilasciato sotto i termini della **Licenza MIT**. Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
