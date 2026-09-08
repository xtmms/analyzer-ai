import time
from typing import Tuple, Dict, Any
from google import genai
from google.genai import types

from core.ai_providers.base import AIProvider
from core.report_schema import get_system_instruction, LogAnalysisReport, build_user_prompt


class GeminiProvider(AIProvider):
    def _client(self) -> "genai.Client":
        return genai.Client(api_key=self.api_key)

    def analyze(self, model: str, logs_payload: str, temperature: float, detail_level: str) -> Tuple[LogAnalysisReport, Dict[str, Any]]:
        client = self._client()
        
        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(detail_level),
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=LogAnalysisReport,
            )
        )
        
        max_retries = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                response = chat.send_message(build_user_prompt(logs_payload))
                break
            except Exception as e:
                err_str = str(e).upper()
                # Riprova solo se è un errore temporaneo 503 (Unavailable) o 429 (Rate Limit)
                if attempt < max_retries - 1 and ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str):
                    wait_time = 2 ** attempt  # Backoff esponenziale: 1s, 2s...
                    time.sleep(wait_time)
                    continue
                raise  # Se non è un errore temporaneo o i tentativi sono finiti, rilancia l'eccezione

        report_obj = response.parsed
        if not isinstance(report_obj, LogAnalysisReport):
            import json
            data = json.loads(response.text)
            report_obj = LogAnalysisReport(**data)
            
        usage = {
            "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
        }

        return report_obj, usage
