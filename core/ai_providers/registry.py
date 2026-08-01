"""
Registro dei provider AI: mappa provider_id -> classe AIProvider, più le
funzioni di stima costi/suggerimento modello più economico, generalizzate
da quelle originariamente specifiche di Gemini in core/gemini_client.py.

Aggiungere un nuovo provider = aggiungerlo a PROVIDER_CLASSES qui e alla
sezione AI_PROVIDERS in config.py: nessun altro modulo va toccato.
"""
from config import AI_PROVIDERS, EXPENSIVE_MODEL_TOKEN_WARNING_THRESHOLD, OUTPUT_TOKENS_ESTIMATE
from core.ai_providers.anthropic_provider import AnthropicProvider
from core.ai_providers.base import AIProvider
from core.ai_providers.gemini_provider import GeminiProvider
from core.ai_providers.openai_provider import OpenAIProvider

PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_provider_class(provider_id: str) -> type[AIProvider]:
    if provider_id not in PROVIDER_CLASSES:
        raise ValueError(f"Provider sconosciuto: {provider_id}")
    return PROVIDER_CLASSES[provider_id]


def build_provider(provider_id: str, api_key: str) -> AIProvider:
    return get_provider_class(provider_id)(api_key)


def list_available_providers(configured_keys: dict[str, str | None]) -> list[dict]:
    """
    Ritorna solo i provider per cui è stata configurata una chiave lato
    backend (configured_keys: provider_id -> chiave o None), così il
    frontend non propone mai un provider che farebbe fallire la richiesta.
    """
    available = []
    for provider_id, cfg in AI_PROVIDERS.items():
        if configured_keys.get(provider_id):
            available.append(
                {
                    "id": provider_id,
                    "label": cfg["label"],
                    "models": cfg["models"],
                    "default_model": cfg["default_model"],
                }
            )
    return available


def estimate_cost(
    token_count: int,
    provider_id: str,
    model: str,
    output_tokens_est: int = OUTPUT_TOKENS_ESTIMATE,
) -> dict:
    """Calcola costo input/output/totale stimato in USD per provider+modello."""
    provider_cfg = AI_PROVIDERS[provider_id]
    pricing_info = provider_cfg["pricing"].get(
        model, provider_cfg["pricing"][provider_cfg["default_model"]]
    )
    input_cost = (token_count / 1_000_000) * pricing_info["input"]
    output_cost = (output_tokens_est / 1_000_000) * pricing_info["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "output_tokens_est": output_tokens_est,
    }


def suggest_cheaper_model(
    token_count: int,
    provider_id: str,
    model: str,
    output_tokens_est: int = OUTPUT_TOKENS_ESTIMATE,
) -> dict | None:
    """
    Se il volume di token supera la soglia di guardia e il modello
    selezionato non è già il più economico dello stesso provider, ritorna
    {"model", "total_cost", "savings_pct"} per suggerire il modello più
    economico dello stesso provider. Ritorna None se non c'è nulla da
    suggerire (nessun risparmio reale, o già sotto soglia).
    """
    if token_count <= EXPENSIVE_MODEL_TOKEN_WARNING_THRESHOLD:
        return None

    pricing = AI_PROVIDERS[provider_id]["pricing"]
    cheapest_model = min(pricing, key=lambda m: pricing[m]["input"] + pricing[m]["output"])
    if cheapest_model == model:
        return None

    current_cost = estimate_cost(token_count, provider_id, model, output_tokens_est)["total_cost"]
    alt_cost = estimate_cost(token_count, provider_id, cheapest_model, output_tokens_est)["total_cost"]
    if current_cost <= 0 or alt_cost >= current_cost:
        return None

    savings_pct = (1 - alt_cost / current_cost) * 100
    return {"model": cheapest_model, "total_cost": alt_cost, "savings_pct": savings_pct}
