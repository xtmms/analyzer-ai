# 🔍 AI Log Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-green.svg)](https://www.python.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)

**AI Log Analyzer** è una moderna e potente applicazione web interattiva sviluppata in **Python** e **Streamlit** che sfrutta i modelli avanzati di **Gemini AI** per assistere SRE, DevOps, sviluppatori e QA Engineer nell'analisi dei log applicativi e infrastrutturali. 

Il tool automatizza l'estrazione delle anomalie, categorizza i messaggi di errore per gravità, stima in tempo reale i costi di utilizzo delle API di intelligenza artificiale ed elabora un report strutturato (Root Cause Analysis e raccomandazioni di fix) ad altissime prestazioni e precisione grazie agli **Structured Outputs** nativi di Google.

---

## 🚀 Caratteristiche Principali

* **Parsing Multiformato & Rilevamento Traceback**: Parsing intelligente dei log con supporto al raggruppamento di stack trace complesse multi-riga (es. Java Spring Boot Exception, Python Tracebacks), evitando la frammentazione del log.
* **Dashboard Statistica Interattiva**: Visualizzazione immediata della ripartizione delle severità dei log (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`) tramite un grafico donut interattivo di **Plotly** e metriche riassuntive.
* **Evidenziatore Sintattico Ultra-Veloce**: Un sistema di colorazione sintattica lato server (Python) che evidenzia severity, logger ed espressioni di file in HTML in meno di 1ms, garantendo zero freeze o rallentamenti nel browser.
* **Structured Outputs con Gemini API (Pydantic)**: Integrazione dello schema rigido `LogAnalysisReport` tramite l'SDK `google-genai`. Le risposte di Gemini vengono fornite direttamente in JSON garantendo che il report finale in 3 punti sia sempre formattato con precisione nelle rispettive schede della UI.
* **Pannello di Stima dei Costi in Tempo Reale**: Calcolo preventivo e dinamico dei costi stimati delle API di input (prompt) e output (risposta) in base alle tariffe ufficiali del listino dei modelli Gemini (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash`), con suggerimenti sul modello più conveniente.
* **Selezione Log Intelligente e Filtri Avanzati**:
  - Filtro multi-selezione per severità di log.
  - Filtro di ricerca testuale dinamico con supporto alle **espressioni regolari (Regex)**.
  - Ordinamento flessibile per selezionare se analizzare le **Prime N** o le **Ultime N** righe (ottimo per isolare il crash finale).
* **Persistenza della Sessione**: I report e i dati generati persistono nello stato di Streamlit anche in caso di re-run causati dall'interazione con l'interfaccia, resettandosi solo al caricamento di un nuovo file.

---

## 🛠️ Tecnologie Utilizzate

* **Python 3.10+** (Testato fino a Python 3.14)
* **Streamlit** (Interfaccia Utente reattiva e orientata alla Dark Mode)
* **Google GenAI SDK** (`google-genai` >= 0.1.1)
* **Plotly Express** (Grafici interattivi)
* **Pydantic v2** (Validazione e garanzia degli output strutturati)

---

## 📋 Prerequisiti

* Python 3.10 o versione successiva.
* Una **Gemini API Key** configurata per le chiamate a Google AI Studio.

---

## 💻 Installazione e Configurazione

1. **Posizionati nella cartella del progetto**:
   ```bash
   cd analyzer-ai
   ```

2. **Inizializza un ambiente virtuale (consigliato)**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Su Windows: .venv\Scripts\activate
   ```

3. **Installa le dipendenze richieste**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura la chiave API**:
   Crea un file `.env` nella cartella radice del progetto e aggiungi la tua chiave:
   ```env
   GEMINI_API_KEY=la_tua_api_key_qui
   ```

---

## 🏃‍♂️ Avvio dell'Applicazione

Una volta configurato l'ambiente virtuale ed il file `.env`, l'interfaccia web si avvia con il comando:
```bash
streamlit run app.py
```
L'applicazione si aprirà automaticamente nel tuo browser all'indirizzo **[http://localhost:8501](http://localhost:8501)**.

---

## 📂 Struttura del Progetto

```
analyzer-ai/
├── app.py                     # Codice sorgente dell'app (UI Streamlit, parser log, Gemini)
├── requirements.txt           # Dipendenze del progetto
├── sample_logs.log            # Log di esempio standard
├── complex_sample_logs.log    # Log di esempio complesso da 500 righe
├── LICENSE                    # Licenza MIT del progetto
└── README.md                  # Questa guida introduttiva
```

---

## 🧑‍💻 Autore

Ideato e sviluppato da:
* **Tommaso Ianniciello** - *Test Automation Engineer*
* **GitHub**: [@xtmms](https://github.com/xtmms)

---

## 📄 Licenza

Questo progetto è rilasciato sotto i termini della **Licenza MIT**. Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
