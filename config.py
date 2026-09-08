"""
Costanti condivise dell'applicazione CLI: severità, modelli Gemini e pricing.
"""

# Ordine e livelli di severità riconosciuti dal parser
SEVERITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

# Livelli di default analizzati (se non specificato diversamente)
DEFAULT_SEVERITY_FILTER = ["CRITICAL", "ERROR", "WARNING"]

# Modelli disponibili e pricing (USD per 1M token).
# NOTA: le tariffe sono il listino ufficiale Google verificato.
AI_PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "models": ["gemini-3.6-flash", "gemini-3.1-pro"],
        "default_model": "gemini-3.6-flash",
        "pricing": {
            "gemini-3.6-flash": {"input": 0.075, "output": 0.30},
            "gemini-3.1-pro": {"input": 1.25, "output": 5.00},
        },
    }
}

DEFAULT_PROVIDER = "gemini"

# Righe massime di default inviate all'AI (bilanciamento costo/contesto)
DEFAULT_MAX_LINES = 200

# Cap sui caratteri di una singola entry (es. traceback enorme) prima dell'invio.
MAX_ENTRY_CHARS = 2000
