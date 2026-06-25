# 🔍 AI Log Analyzer with Gemini API

AI Log Analyzer è un'applicazione web interattiva sviluppata in **Python** con **Streamlit** che consente a sviluppatori, DevOps, SRE, tester e QA engineer di caricare file di log di qualsiasi genere, isolare automaticamente anomalie ed errori, ed analizzarli istantaneamente tramite l'**API di Gemini** per ricevere un report strutturato e azionabile.

## 🚀 Caratteristiche Principali

- **Caricamento File Semplice**: Trascina e rilascia file di log in formato `.txt` o `.log`.
- **Filtro Intelligente delle Anomalie**: Estrazione automatica e classificazione delle righe contenenti livelli di severità critici (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`).
- **Parsing delle Stack Trace**: Rilevamento automatico di traceback multi-riga (es. Java, Python) per mantenere integro il contesto dell'errore.
- **Report Strutturato in 3 Punti con Gemini**:
  - **Sintesi delle Problematiche**: Panoramica ad alto livello degli eventi anomali rilevati e del loro impatto.
  - **Analisi Tecnica e Cause Radice (Root Cause Analysis)**: Spiegazione tecnica dettagliata sulle cause basandosi sui messaggi e i traceback forniti.
  - **Piano di Azione e Risoluzione**: Raccomandazioni pratiche, correzioni di bug, modifiche infrastrutturali o configurazioni di sistema.
- **Controllo Parametri**: Scelta del modello (`gemini-2.5-flash` o `gemini-2.5-pro`), regolazione della temperatura e personalizzazione delle parole chiave del filtro direttamente dalla UI.
- **Esportazione in Markdown**: Possibilità di scaricare il report generato con un click.

---

## 🛠️ Tecnologie Utilizzate

- **Python 3.14+**
- **Streamlit** (UI Reattiva e Moderna)
- **Google GenAI SDK** (`google-genai`)
- **RegEx** per il filtraggio e l'estrazione strutturata dei testi

---

## 📋 Prerequisiti

Assicurati di avere installato sul tuo sistema:
- Python 3.10 o superiore (testato con Python 3.14)
- Un account Google AI Studio per ottenere una **Gemini API Key** (gratuita)

---

## 💻 Installazione e Configurazione

1. **Clona la repository** o posizionati nella cartella del progetto:
   ```bash
   cd analyzer-ai
   ```

2. **Crea un ambiente virtuale**:
   ```bash
   python3 -m venv .venv
   ```

3. **Attiva l'ambiente virtuale**:
   - **Su macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
   - **Su Windows**:
     ```cmd
     .venv\Scripts\activate
     ```

4. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configura la chiave API (Obbligatoria)**:
   Crea un file chiamato `.env` nella directory principale del progetto e inserisci la tua chiave API di Gemini:
   ```env
   GEMINI_API_KEY=la_tua_api_key_qui
   ```
   *Nota: Per ragioni di sicurezza, l'applicazione non permette l'inserimento manuale della chiave API tramite l'interfaccia utente; deve essere configurata obbligatoriamente a livello di sistema o tramite file `.env`.*

---

## 🏃‍♂️ Avvio dell'Applicazione

Una volta configurato l'ambiente, avvia l'interfaccia web con il comando:
```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo **[http://localhost:8501](http://localhost:8501)**.

---

## 📂 Struttura del Progetto

```
analyzer-ai/
├── app.py                # Codice dell'applicazione Streamlit (UI, parser e integrazione Gemini)
├── requirements.txt      # Dipendenze del progetto
├── sample_logs.log       # File di log di esempio per i test
├── .gitignore            # File per escludere file temporanei e chiavi API da Git
└── README.md             # Questo documento informativo
```

---

## 📝 Esempio di Utilizzo

Per testare subito l'applicazione:
1. Assicurati che la chiave API sia configurata nel file `.env`.
2. Avvia l'app e trascina il file di esempio `sample_logs.log` incluso nel progetto.
3. Controlla le righe di errore estratte nell'area di anteprima.
4. Clicca su **Genera Report di Analisi con Gemini** e attendi l'output strutturato!
