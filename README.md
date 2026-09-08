# Analyzer AI CLI

Strumento da riga di comando "One-Shot" per l'analisi intelligente e automatizzata dei file di log.
Utilizza modelli LLM per analizzare log complessi o stack trace estese, fornendo una "Root Cause Analysis" dettagliata e sintesi dei problemi in markdown.

## Funzionalità Principali (Enterprise Ready)
- **Data Masking Automatico**: Oscura automaticamente dati sensibili (PII) come indirizzi IPv4, email, UUID e token JWT (Bearer) prima dell'invio ai provider AI per garantire sicurezza e privacy.
- **Smart Truncation**: Ottimizza il consumo di token su log di grandi dimensioni dando priorità a eccezioni e stack trace, tagliando le righe non utili per il debug.
- **Supporto Pipeline (Stdin)**: Accetta log direttamente da `stdin` (`cat`, `kubectl`, `tail`), ideale per CI/CD o concatenazione bash.
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
# Esecuzione standard con file
python main.py --file logs/app.log --provider gemini --model gemini-3.6-flash --detail Dettagliato

# Esecuzione tramite Stdin con Hint e Print a schermo
cat logs/app.log | python main.py --hint "Riavviato il pod database" --print
```

### Parametri aggiuntivi
- `--hint "testo"`: Fornisce all'LLM un suggerimento o contesto per indirizzare meglio la diagnosi.
- `--print`: Esegue il rendering formattato in Markdown a colori direttamente nella console al termine dell'analisi.

## Output Raggruppato
Il risultato dell'analisi verrà generato in una sottocartella dedicata sotto la cartella `output/` (es. `output/run_20260908_184500_app_log/`).
All'interno troverai:
- `report.md`: L'analisi dettagliata (sintesi, root cause, raccomandazioni).
- `masked_input.log`: Il file inviato all'LLM, privo dei tuoi dati sensibili, per motivi di audit.

