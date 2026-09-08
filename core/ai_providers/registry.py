"""
Registro dei provider AI: mappa provider_id -> classe AIProvider
e funzioni di stima/calcolo dei costi.
"""
from config import AI_PROVIDERS
from core.ai_providers.base import AIProvider
from core.ai_providers.gemini_provider import GeminiProvider

PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
}

def get_provider_class(provider_id: str) -> type[AIProvider]:
    if provider_id not in PROVIDER_CLASSES:
        raise ValueError(f"Provider sconosciuto: {provider_id}")
    return PROVIDER_CLASSES[provider_id]

def build_provider(provider_id: str, api_key: str) -> AIProvider:
    return get_provider_class(provider_id)(api_key)

def calculate_cost(
    provider_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """Calcola il costo finale in USD in base all'uso reale."""
    provider_cfg = AI_PROVIDERS.get(provider_id)
    if not provider_cfg:
        return {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}

    pricing_info = provider_cfg["pricing"].get(
        model, provider_cfg["pricing"][provider_cfg["default_model"]]
    )
    input_cost = (input_tokens / 1_000_000) * pricing_info["input"]
    output_cost = (output_tokens / 1_000_000) * pricing_info["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }
