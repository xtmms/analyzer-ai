from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from core.report_schema import LogAnalysisReport

class AIProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def analyze(self, model: str, logs_payload: str, temperature: float, detail_level: str, hint: str = None) -> Tuple[LogAnalysisReport, Dict[str, Any]]:
        """Invia i log al provider e ritorna (LogAnalysisReport, UsageMetadata)."""
        raise NotImplementedError
