"""
Provider Google Gemini (google-genai SDK). Conteggio token reale via
client.models.count_tokens(), con fallback euristico se la chiamata fallisce
(nessuna chiave, rete assente, rate limit) così la UI non si blocca mai.
"""
from google import genai
from google.genai import types

from core.ai_providers.base import AIProvider, estimate_tokens_heuristic
from core.report_schema import SYSTEM_INSTRUCTION, LogAnalysisReport, build_user_prompt


class GeminiProvider(AIProvider):
    def _client(self) -> "genai.Client":
        return genai.Client(api_key=self.api_key)

    def count_tokens(self, model: str, text: str) -> tuple[int, bool]:
        try:
            client = self._client()
            result = client.models.count_tokens(model=model, contents=text)
            return result.total_tokens, True
        except Exception:
            return estimate_tokens_heuristic(text), False

    def analyze(self, model: str, logs_payload: str, temperature: float) -> LogAnalysisReport:
        client = self._client()
        response = client.models.generate_content(
            model=model,
            contents=build_user_prompt(logs_payload),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=LogAnalysisReport,
            ),
        )

        report_obj = response.parsed
        if not isinstance(report_obj, LogAnalysisReport):
            import json

            data = json.loads(response.text)
            report_obj = LogAnalysisReport(**data)

        return report_obj
