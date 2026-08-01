"""
Provider OpenAI. Structured output via JSON Schema mode (response_format),
conteggio token via tiktoken (tokenizer ufficiale locale: non esiste un
endpoint di conteggio remoto per questo provider, quindi qui "reale"
significa tokenizzazione locale accurata, non una chiamata di rete).
"""
import json

import tiktoken
from openai import OpenAI

from core.ai_providers.base import AIProvider, estimate_tokens_heuristic
from core.report_schema import (
    LOG_ANALYSIS_JSON_SCHEMA,
    SYSTEM_INSTRUCTION,
    LogAnalysisReport,
    build_user_prompt,
)


class OpenAIProvider(AIProvider):
    def _client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key)

    def count_tokens(self, model: str, text: str) -> tuple[int, bool]:
        try:
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("o200k_base")
            return len(encoding.encode(text)), True
        except Exception:
            return estimate_tokens_heuristic(text), False

    def analyze(self, model: str, logs_payload: str, temperature: float) -> LogAnalysisReport:
        client = self._client()
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": build_user_prompt(logs_payload)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "log_analysis_report",
                    "schema": LOG_ANALYSIS_JSON_SCHEMA,
                    "strict": True,
                },
            },
        )
        data = json.loads(response.choices[0].message.content)
        return LogAnalysisReport(**data)
