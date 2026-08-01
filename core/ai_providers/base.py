"""
Interfaccia comune implementata da ogni provider AI (Gemini, OpenAI,
Anthropic...). Il backend dipende solo da questa interfaccia, mai
dall'SDK di uno specifico provider: aggiungere un nuovo provider significa
implementare questa classe e registrarla in registry.py, senza toccare il
resto del codice (route, quota, storico).
"""
from abc import ABC, abstractmethod

from core.report_schema import LogAnalysisReport


class AIProvider(ABC):
    """Costruito con la API key del provider (letta lato backend da env,
    mai fornita dal client)."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def count_tokens(self, model: str, text: str) -> tuple[int, bool]:
        """Ritorna (numero_token, is_real). is_real=True se il conteggio
        viene da un meccanismo affidabile specifico del provider (API di
        conteggio o tokenizer ufficiale locale), False se è una stima
        euristica di fallback (usata solo quando il meccanismo primario
        fallisce, es. rete assente o rate limit)."""
        raise NotImplementedError

    @abstractmethod
    def analyze(self, model: str, logs_payload: str, temperature: float) -> LogAnalysisReport:
        """Invia i log al provider e ritorna un LogAnalysisReport. Solleva
        eccezioni specifiche dell'SDK: il chiamante (route FastAPI) le
        traduce in risposte HTTP appropriate."""
        raise NotImplementedError


def estimate_tokens_heuristic(text: str) -> int:
    """Fallback grossolano (~4 caratteri per token), condiviso da tutti i
    provider quando il conteggio primario non è disponibile."""
    return len(text) // 4
