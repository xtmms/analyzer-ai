# Analyzer AI CLI

Strumento da riga di comando per l'analisi intelligente dei file di log.
Utilizza modelli LLM per analizzare log complessi o stack trace estese, fornendo una "Root Cause Analysis" dettagliata e sintesi dei problemi in markdown.

## Requisiti
- Python 3.10+
- Installare i requisiti con `pip install -r requirements.txt`

## Configurazione
Crea un file `.env` nella root del progetto o esporta le variabili d'ambiente necessarie:
```bash
GEMINI_API_KEY="la-tua-chiave-api-gemini"
```

## Utilizzo Modalità Interattiva
Basta lanciare il comando senza argomenti per essere guidati nella scelta del file e del modello:
```bash
python main.py
```

## Utilizzo Modalità Headless (Agenti / Script)
Puoi passare gli argomenti direttamente per by-passare il prompt interattivo:
```bash
python main.py --file logs/app.log --provider gemini --model gemini-3.6-flash --detail Dettagliato
```

## Output
Il risultato dell'analisi verrà generato in automatico sotto la cartella `output/` in formato Markdown. Al termine dell'esecuzione verrà stampato un sommario dell'uso dei token reali e il costo stimato.

## Distribuzione dal Cliente

Se i log risiedono nei server di un cliente, hai due modi ideali per distribuire e usare questo tool senza inquinare o modificare le dipendenze del loro sistema:

### Opzione 1: Docker (Ideale se il cliente ha Docker installato)
Puoi eseguire il tool via Docker montando la cartella dei log del cliente.
```bash
# 1. Build dell'immagine
docker build -t analyzer-ai .

# 2. Esecuzione (montando la cartella logs locale del cliente su /logs dentro il container)
docker run --rm -it \
    -e GEMINI_API_KEY="tua-chiave-api" \
    -v /percorso/log/cliente:/logs \
    -v $(pwd)/output:/app/output \
    analyzer-ai --file /logs/error.log
```

### Opzione 2: Eseguibile Standalone (PyInstaller)
Se il cliente **non ha Docker** e non vuoi installare Python, puoi trasformare questo tool in un singolo file eseguibile nativo (es. `.exe` o `.elf`) che contiene Python e tutte le dipendenze.

1. Installa PyInstaller: `pip install pyinstaller`
2. Compila il tool: `pyinstaller --onefile main.py --name analyzer-cli`
3. Troverai un file `analyzer-cli` nella cartella `dist/`. Passa quel singolo file al cliente (o via scp sul server) e potrà essere eseguito come un normale comando Unix:
   `./analyzer-cli --file /var/log/syslog`
