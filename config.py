"""
Costanti condivise dell'applicazione: severità, colori, modelli e pricing.

Questo modulo non ha dipendenze da Streamlit o dall'SDK Gemini: è puro
dato di configurazione, così un agente (o uno sviluppatore) può leggerlo
in isolamento senza dover caricare il resto dell'app.
"""

# Ordine e livelli di severità riconosciuti dal parser
SEVERITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

DEFAULT_SEVERITY_FILTER = ["CRITICAL", "ERROR", "WARNING"]

# Colori per badge, syntax highlighting e grafico a torta (single source of truth:
# in precedenza questo dizionario era duplicato 3 volte in app.py)
SEVERITY_COLORS = {
    "CRITICAL": "#ff5555",
    "FATAL": "#ff5555",
    "SEVERE": "#ff5555",
    "ERROR": "#ff6e6e",
    "FAIL": "#ff6e6e",
    "FAILED": "#ff6e6e",
    "EXCEPTION": "#ff6e6e",
    "WARNING": "#ffb86c",
    "WARN": "#ffb86c",
    "INFO": "#50fa7b",
    "DEBUG": "#8be9fd",
}

# Sottoinsieme usato per badge/grafico (solo i 5 livelli canonici)
SEVERITY_CHART_COLORS = {level: SEVERITY_COLORS[level] for level in SEVERITY_LEVELS}

# Provider AI disponibili, coi rispettivi modelli e pricing (USD per 1M token).
# Ogni provider_id qui deve avere una classe corrispondente in
# core/ai_providers/registry.py. Un provider compare nella UI solo se il
# backend ha la relativa chiave API configurata (vedi backend/app/settings.py).
#
# NOTA: le tariffe "gemini" sono il listino ufficiale Google verificato.
# Le tariffe "openai" e "anthropic" sono SEGNAPOSTO indicativi: vanno
# confermate contro le pricing page ufficiali dei rispettivi provider prima
# di andare in produzione — non usarle per fatturazione reale senza verifica.
AI_PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-2.5-flash",
        "pricing": {
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        },
    },
    "openai": {
        "label": "OpenAI",
        "models": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        "default_model": "gpt-4.1-mini",
        "pricing": {
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1": {"input": 2.00, "output": 8.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        },
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "models": ["claude-sonnet-5", "claude-haiku-4-5", "claude-opus-5"],
        "default_model": "claude-sonnet-5",
        "pricing": {
            "claude-sonnet-5": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
            "claude-opus-5": {"input": 15.00, "output": 75.00},
        },
    },
}

DEFAULT_PROVIDER = "gemini"

OUTPUT_TOKENS_ESTIMATE = 500

# Oltre questa soglia di token stimati, se il modello selezionato è il più
# costoso del provider suggeriamo di passare al più economico dello stesso
# provider per risparmiare sui costi.
EXPENSIVE_MODEL_TOKEN_WARNING_THRESHOLD = 5000

# Righe massime di default inviate all'AI (bilanciamento costo/contesto)
DEFAULT_MAX_LINES = 200

# Cap sui caratteri di una singola entry (es. traceback enorme) prima dell'invio.
# Riduce lo spreco di token su stack trace ripetitive o abnormemente lunghe.
MAX_ENTRY_CHARS = 2000
