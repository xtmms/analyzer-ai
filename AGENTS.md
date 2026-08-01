# AGENTS.md — mappa del repo per agenti AI

Questo file esiste per evitare che un agente debba leggere l'intero codebase
per orientarsi. Leggi solo il modulo che ti serve per il task che hai in mano.

## Cos'è il progetto

SaaS multi-utente: un backend FastAPI (`backend/`) espone API di auth, parsing
log, stima costi e analisi AI; un frontend React (`frontend/`) le consuma.
Ogni utente ha un account, un piano con quota mensile di analisi e uno
storico persistente. Il backend invia un sottoinsieme di righe di log a uno
tra più provider AI (Google Gemini, OpenAI, Anthropic — scelti dall'utente,
chiavi configurate lato server) per generare un report strutturato.

Nessun modulo `core/` importa FastAPI o React; nessun modulo `core/` fa I/O
di rete tranne `core/ai_providers/*_provider.py`. Questo è intenzionale:
`core/` deve restare testabile senza un server o una chiave API.

## Mappa dei moduli — leggi solo quello che ti serve

| File/directory | Cosa contiene | Quando aprirlo |
|---|---|---|
| `config.py` | Costanti: severità, colori, provider AI (`AI_PROVIDERS`), pricing, soglie | Cambi un modello, un prezzo, una soglia, un colore |
| `core/log_parser.py` | Parsing log, filtri, dedupe, troncamento | Modifichi come i log vengono interpretati o preparati per l'invio |
| `core/formatting.py` | Syntax highlighting log, markdown→HTML, export .md | Cambi come viene formattato il testo |
| `core/report_schema.py` | Schema Pydantic condiviso del report (`LogAnalysisReport`) | Cambi la forma del report AI |
| `core/ai_providers/base.py` | Interfaccia `AIProvider` comune a tutti i provider | Capisci il contratto prima di aggiungerne uno nuovo |
| `core/ai_providers/{gemini,openai,anthropic}_provider.py` | Integrazione specifica di ogni provider | Tocchi l'integrazione con un provider AI esistente |
| `core/ai_providers/registry.py` | Mappa provider→classe, stima costi, suggerimento modello più economico | Aggiungi un nuovo provider, cambi la logica di pricing |
| `backend/app/settings.py` | Config da env/.env: JWT, DB, chiavi provider, quota piani | Aggiungi una variabile di configurazione |
| `backend/app/models.py` | Modelli SQLAlchemy: `User`, `UsageCounter`, `AnalysisRecord` | Cambi lo schema dati persistito |
| `backend/app/quota.py` | Logica limiti mensili per piano free/pro | Cambi le regole di quota |
| `backend/app/auth.py` | Password hashing, JWT, `get_current_user` | Tocchi l'autenticazione |
| `backend/app/routes/*.py` | Endpoint FastAPI (auth, providers, logs, history, usage) | Aggiungi/modifichi un endpoint |
| `frontend/src/pages/*.tsx` | Pagine React (Landing, Login, Register, Dashboard, History) | Cambi una schermata |
| `frontend/src/components/*.tsx` | Componenti riutilizzabili (filtri, card, grafici, selettori) | Cambi un pezzo di UI riusato in più pagine |
| `frontend/src/lib/api.ts` | Client HTTP tipizzato verso il backend | Aggiungi/modifichi una chiamata API |
| `frontend/src/lib/auth-context.tsx` | Stato auth globale (token JWT, utente corrente) | Tocchi login/logout/sessione |

## Convenzioni

- Le funzioni pure (no side effect, no FastAPI/React) vivono in `core/` e
  sono coperte da test in `tests/`. Se aggiungi logica di parsing/costo,
  aggiungi anche il test corrispondente nello stesso PR.
- Le costanti duplicate (colori severità, pricing, soglie) vivono **solo**
  in `config.py`: non reintrodurre duplicazioni in `backend/` o `frontend/`
  (in TypeScript, `frontend/src/lib/types.ts` rispecchia manualmente i
  valori di `config.py` — tienili sincronizzati se cambi l'uno o l'altro).
- Un nuovo provider AI = una nuova classe in `core/ai_providers/` che
  implementa `AIProvider` + una entry in `PROVIDER_CLASSES`
  (`core/ai_providers/registry.py`) + una entry in `config.AI_PROVIDERS`.
  Nessun altro modulo va toccato per il solo aggiungere un provider.
- Le chiavi dei provider AI sono **sempre lato server** (`backend/app/settings.py`,
  lette da `.env`): non introdurre un modo per l'utente di fornire una
  propria chiave dal frontend, romperebbe il modello SaaS.
- `backend/app/quota.py` è l'unico punto che decide se un utente può fare
  un'altra analisi: non duplicare il controllo altrove.
- Il frontend usa `localStorage` per il JWT (`frontend/src/lib/api.ts`,
  `TOKEN_STORAGE_KEY`) e un React Context (`auth-context.tsx`) come unica
  fonte di verità per lo stato utente lato client.

## Ottimizzazione token (in `core/log_parser.prepare_entries_for_send()`)

Prima di inviare i log a un provider AI, la pipeline applica, in ordine:

1. **Dedupe** (`dedupe_entries`): righe consecutive identiche (a meno del
   timestamp) vengono compresse con un contatore `[ripetuta xN]`.
2. **Truncate** (`truncate_entry_text`): entry singole oltre
   `config.MAX_ENTRY_CHARS` (default 2000) vengono troncate a testa+coda.

Il conteggio token mostrato in UI usa il meccanismo "reale" di ciascun
provider (`count_tokens` dell'API per Gemini/Anthropic, tokenizer locale
`tiktoken` per OpenAI), con fallback automatico a `len(testo)//4` se il
meccanismo primario fallisce — vedi `core/ai_providers/*_provider.py` e
`core/ai_providers/base.estimate_tokens_heuristic`. Non ripristinare la sola
euristica come fonte primaria: è imprecisa su testo non inglese e su log con
molta punteggiatura/simboli.

## Come eseguire

```bash
cp .env.example .env   # valorizza almeno una chiave provider AI
pip install -r requirements-dev.txt
pytest                                        # core/ + backend/tests/, nessuna rete richiesta
uvicorn backend.app.main:app --reload         # API su :8000

cd frontend && npm install && npm run dev     # UI su :5173
```

## Cosa NON fare

- Non chiamare l'SDK di un provider AI (`google-genai`, `openai`,
  `anthropic`) da dentro `core/log_parser.py`, `core/formatting.py` o da un
  componente `frontend/`: le chiamate di rete verso i provider restano
  isolate in `core/ai_providers/*_provider.py`, invocate solo da
  `backend/app/routes/logs.py`.
- Non aggiungere dipendenze runtime a `tests/` o `backend/tests/`: i test
  devono girare senza chiave API e senza rete (i provider sono sempre
  mockati nei test — vedi `backend/tests/test_logs_route.py` per il
  pattern).
- Non introdurre un secondo posto dove viene deciso il pricing o la quota:
  `core/ai_providers/registry.py` (costi) e `backend/app/quota.py` (limiti)
  sono le uniche fonti di verità.
