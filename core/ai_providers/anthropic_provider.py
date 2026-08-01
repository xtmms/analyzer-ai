"""
Provider Anthropic Claude. Non esiste una modalità di structured output
nativa equivalente a quella di Gemini/OpenAI: lo schema viene fatto
rispettare forzando una tool call (tool_choice) il cui input_schema è
LOG_ANALYSIS_JSON_SCHEMA, e si legge il risultato dal blocco tool_use della
risposta. Conteggio token reale via client.messages.count_tokens().
"""
from anthropic import Anthropic

from core.ai_providers.base import AIProvider, estimate_tokens_heuristic
from core.report_schema import (
    LOG_ANALYSIS_JSON_SCHEMA,
    SYSTEM_INSTRUCTION,
    LogAnalysisReport,
    build_user_prompt,
)

_TOOL_NAME = "submit_log_analysis_report"


class AnthropicProvider(AIProvider):
    def _client(self) -> Anthropic:
        return Anthropic(api_key=self.api_key)

    def count_tokens(self, model: str, text: str) -> tuple[int, bool]:
        try:
            client = self._client()
            result = client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}],
            )
            return result.input_tokens, True
        except Exception:
            return estimate_tokens_heuristic(text), False

    def analyze(self, model: str, logs_payload: str, temperature: float) -> LogAnalysisReport:
        client = self._client()
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=temperature,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": build_user_prompt(logs_payload)}],
            tools=[
                {
                    "name": _TOOL_NAME,
                    "description": "Invia il report di analisi log strutturato.",
                    "input_schema": LOG_ANALYSIS_JSON_SCHEMA,
                }
            ],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == _TOOL_NAME:
                return LogAnalysisReport(**block.input)

        raise ValueError("Anthropic non ha restituito la tool call attesa per il report.")
