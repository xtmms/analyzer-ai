# AGENTS.md — mappa del repo per agenti AI

Questo tool CLI analizza log tramite chiamate a provider AI (Gemini). Può essere usato da agenti come strumento headless.

## Mappa dei moduli

| File | Cosa contiene |
|---|---|
| `main.py` | Entrypoint CLI (Argparse, Prompt interattivi, calcolo finale costi). |
| `config.py` | Costanti: severità, config dei modelli e pricing. |
| `core/log_parser.py` | Parsing log, filtri, dedupe, troncamento testati. |
| `core/formatting.py` | Trasforma l'oggetto Pydantic in Markdown e lo salva in `output/`. |
| `core/report_schema.py` | Schema Pydantic condiviso del report AI e istruzioni di sistema. |
| `core/ai_providers/base.py` | Interfaccia base per i provider AI. |
| `core/ai_providers/gemini_provider.py` | Integrazione con Gemini SDK. |
| `core/ai_providers/registry.py` | Calcolo costi finali. |

## Come eseguire (Headless)
```bash
python main.py --file path/to/log.txt --provider gemini --model gemini-3.6-flash --detail Sintetico
```

Output: Markdown in cartella `output/`.
