# Test Automation AI Analyzer CLI

Strumento da riga di comando "One-Shot" per l'analisi intelligente e automatizzata dei fallimenti dei test (Test Automation).
Utilizza modelli LLM per analizzare report strutturati (JUnit XML, JSON) o log testuali grezzi, fornendo un report dettagliato per il QA che include test falliti, root cause analysis, flakiness assessment e raccomandazioni precise per il fix.

## Funzionalità Principali (Enterprise Ready)
- **Smart Parsing (XML & JSON)**: Rileva automaticamente i file XML (JUnit) e JSON (es. Cypress, Playwright) estraendo unicamente gli stack trace dei test falliti per eliminare il rumore e risparmiare token.
- **Data Masking Automatico**: Oscura automaticamente dati sensibili (PII) come indirizzi IPv4, email, UUID e token JWT (Bearer) prima dell'invio ai provider AI.
- **Supporto Pipeline (Stdin)**: Accetta log crudi direttamente da `stdin` (es. l'output di un test runner in locale o in CI), scalando dinamicamente il parsing riga per riga se il formato non è strutturato.
- **Audit Logging**: Conserva il payload esatto "mascherato" generato per ogni esecuzione.

## Requisiti
- Python 3.10+
- Installare i requisiti con `pip install -r requirements.txt`

## Configurazione
Crea un file `.env` nella root del progetto o esporta le variabili d'ambiente necessarie:
```bash
GEMINI_API_KEY="la-tua-chiave-api-gemini"
```

## Utilizzo Modalità Interattiva
Basta lanciare il comando senza argomenti per essere guidati visivamente:
```bash
python main.py
```
*(In modalità interattiva ti verrà data la possibilità di inserire un hint per l'AI e il report verrà automaticamente stampato nel terminale).*

## Utilizzo Modalità Headless e Standard Input (Stdin)
Puoi passare gli argomenti direttamente per by-passare il prompt interattivo, oppure fare pipe dell'output:

```bash
# Esecuzione standard con report XML (es. JUnit)
python main.py --file reports/junit.xml --provider gemini --model gemini-3.6-flash --detail Dettagliato

# Esecuzione tramite Stdin per log testuali
pytest --tb=short | python main.py --hint "Analizza i test E2E falliti." --print
```

### Parametri aggiuntivi
- `--hint "testo"`: Fornisce all'LLM un suggerimento o contesto per indirizzare meglio la diagnosi.
- `--print`: Esegue il rendering formattato in Markdown a colori direttamente nella console al termine dell'analisi.

## Output Raggruppato
Il risultato dell'analisi verrà generato in una sottocartella dedicata sotto la cartella `output/` (es. `output/run_20260908_184500_junit_xml/`).
All'interno troverai:
- `report.md`: L'analisi AI per il QA (test falliti, root cause, flakiness, raccomandazioni).
- `masked_input.log`: I test falliti inviati all'LLM, privi dei tuoi dati sensibili, per motivi di audit.
