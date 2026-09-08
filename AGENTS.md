# AGENTS.md — mappa del repo per agenti AI

Questo tool CLI analizza fallimenti di test e test report (XML/JSON/raw) tramite chiamate a provider AI (Gemini). Può essere usato da agenti come strumento headless per valutare risultati QA.

## Mappa dei moduli

| File | Cosa contiene |
|---|---|
| `main.py` | Entrypoint CLI (Argparse, Prompt interattivi, calcolo finale costi). |
| `config.py` | Costanti: severità, config dei modelli e pricing. |
| `core/log_parser.py` | Parsing report (JUnit XML, JSON) e raw log, estrazione test falliti, filtri, dedupe, troncamento testati. |
| `core/formatting.py` | Trasforma l'oggetto Pydantic in Markdown e lo salva in `output/`. |
| `core/report_schema.py` | Schema Pydantic del QA report (TestAutomationReport) e istruzioni di sistema per SDET. |
| `core/ai_providers/base.py` | Interfaccia base per i provider AI. |
| `core/ai_providers/gemini_provider.py` | Integrazione con Gemini SDK usando TestAutomationReport. |
| `core/ai_providers/registry.py` | Calcolo costi finali. |

## Come eseguire (Headless)
```bash
python main.py --file path/to/junit.xml --provider gemini --model gemini-3.6-flash --detail Sintetico
```

Output: Markdown in cartella `output/`.
