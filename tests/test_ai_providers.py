"""
Test delle funzioni pure di core/ai_providers/ (registry, pricing) e della
logica di parsing di ogni provider. Nessuna chiamata di rete reale: le
chiamate agli SDK vengono mockate sostituendo il metodo `_client()` di
ciascun provider (o `tiktoken` per OpenAI), come da convenzione in
AGENTS.md — i test girano senza chiave API e senza rete.
"""
import json

import pytest

from core.ai_providers.anthropic_provider import AnthropicProvider
from core.ai_providers.base import estimate_tokens_heuristic
from core.ai_providers.gemini_provider import GeminiProvider
from core.ai_providers.openai_provider import OpenAIProvider
from core.ai_providers.registry import (
    build_provider,
    estimate_cost,
    get_provider_class,
    list_available_providers,
    suggest_cheaper_model,
)
from core.report_schema import LogAnalysisReport, ReportPoint

_SAMPLE_REPORT_PAYLOAD = {
    "problem_summary": {"title": "t1", "content": "c1"},
    "root_cause_analysis": {"title": "t2", "content": "c2"},
    "recommendations": {"title": "t3", "content": "c3"},
}


def _sample_report() -> LogAnalysisReport:
    return LogAnalysisReport(
        problem_summary=ReportPoint(title="t1", content="c1"),
        root_cause_analysis=ReportPoint(title="t2", content="c2"),
        recommendations=ReportPoint(title="t3", content="c3"),
    )


# --- base.py ---------------------------------------------------------------


def test_estimate_tokens_heuristic():
    assert estimate_tokens_heuristic("a" * 400) == 100
    assert estimate_tokens_heuristic("") == 0


# --- registry.py -------------------------------------------------------------


def test_get_provider_class_known_ids():
    assert get_provider_class("gemini") is GeminiProvider
    assert get_provider_class("openai") is OpenAIProvider
    assert get_provider_class("anthropic") is AnthropicProvider


def test_get_provider_class_unknown_raises():
    with pytest.raises(ValueError):
        get_provider_class("does-not-exist")


def test_build_provider_sets_api_key():
    provider = build_provider("gemini", "fake-key")
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "fake-key"


def test_list_available_providers_filters_by_configured_keys():
    configured = {"gemini": "key123", "openai": None, "anthropic": ""}
    available = list_available_providers(configured)
    assert [p["id"] for p in available] == ["gemini"]


def test_estimate_cost_flash_cheaper_than_pro():
    flash_cost = estimate_cost(1_000_000, "gemini", "gemini-2.5-flash")["total_cost"]
    pro_cost = estimate_cost(1_000_000, "gemini", "gemini-2.5-pro")["total_cost"]
    assert flash_cost < pro_cost


def test_suggest_cheaper_model_triggers_above_threshold():
    suggestion = suggest_cheaper_model(token_count=10_000, provider_id="gemini", model="gemini-2.5-pro")
    assert suggestion is not None
    assert suggestion["model"] == "gemini-2.5-flash"
    assert suggestion["savings_pct"] > 0


def test_suggest_cheaper_model_none_for_already_cheapest():
    assert suggest_cheaper_model(token_count=10_000, provider_id="gemini", model="gemini-2.5-flash") is None


def test_suggest_cheaper_model_none_below_threshold():
    assert suggest_cheaper_model(token_count=100, provider_id="gemini", model="gemini-2.5-pro") is None


# --- gemini_provider.py ------------------------------------------------------


def test_gemini_provider_count_tokens_falls_back_on_error(monkeypatch):
    provider = GeminiProvider(api_key="fake")
    monkeypatch.setattr(provider, "_client", lambda: (_ for _ in ()).throw(RuntimeError("no network")))
    count, is_real = provider.count_tokens("gemini-2.5-flash", "a" * 400)
    assert is_real is False
    assert count == 100


def test_gemini_provider_analyze_returns_parsed_report(monkeypatch):
    provider = GeminiProvider(api_key="fake")
    fake_report = _sample_report()

    class _FakeResponse:
        parsed = fake_report
        text = ""

    class _FakeModels:
        def generate_content(self, **kwargs):
            return _FakeResponse()

    class _FakeClient:
        models = _FakeModels()

    monkeypatch.setattr(provider, "_client", lambda: _FakeClient())
    result = provider.analyze("gemini-2.5-flash", "log line", 0.2)
    assert result == fake_report


# --- openai_provider.py -------------------------------------------------------


class _FakeEncoding:
    def encode(self, text: str) -> list:
        return list(text)


def test_openai_provider_count_tokens_uses_tiktoken(monkeypatch):
    provider = OpenAIProvider(api_key="fake")
    monkeypatch.setattr(
        "core.ai_providers.openai_provider.tiktoken.encoding_for_model",
        lambda model: _FakeEncoding(),
    )
    count, is_real = provider.count_tokens("gpt-4.1-mini", "abcd")
    assert is_real is True
    assert count == 4


def test_openai_provider_count_tokens_falls_back_on_error(monkeypatch):
    provider = OpenAIProvider(api_key="fake")

    def _raise(*args, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr("core.ai_providers.openai_provider.tiktoken.encoding_for_model", _raise)
    monkeypatch.setattr("core.ai_providers.openai_provider.tiktoken.get_encoding", _raise)
    count, is_real = provider.count_tokens("gpt-4.1-mini", "a" * 400)
    assert is_real is False
    assert count == 100


def test_openai_provider_analyze_parses_json_response(monkeypatch):
    provider = OpenAIProvider(api_key="fake")

    class _Message:
        content = json.dumps(_SAMPLE_REPORT_PAYLOAD)

    class _Choice:
        message = _Message()

    class _FakeResponse:
        choices = [_Choice()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    monkeypatch.setattr(provider, "_client", lambda: _FakeClient())
    result = provider.analyze("gpt-4.1-mini", "log line", 0.2)
    assert result.problem_summary.title == "t1"
    assert result.recommendations.content == "c3"


# --- anthropic_provider.py -----------------------------------------------------


def test_anthropic_provider_count_tokens_falls_back_on_error(monkeypatch):
    provider = AnthropicProvider(api_key="fake")
    monkeypatch.setattr(provider, "_client", lambda: (_ for _ in ()).throw(RuntimeError("no network")))
    count, is_real = provider.count_tokens("claude-sonnet-5", "a" * 400)
    assert is_real is False
    assert count == 100


def test_anthropic_provider_analyze_reads_tool_use_block(monkeypatch):
    provider = AnthropicProvider(api_key="fake")

    class _Block:
        type = "tool_use"
        name = "submit_log_analysis_report"
        input = _SAMPLE_REPORT_PAYLOAD

    class _FakeResponse:
        content = [_Block()]

    class _FakeMessages:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeClient:
        messages = _FakeMessages()

    monkeypatch.setattr(provider, "_client", lambda: _FakeClient())
    result = provider.analyze("claude-sonnet-5", "log line", 0.2)
    assert result.recommendations.content == "c3"


def test_anthropic_provider_analyze_raises_without_tool_use_block(monkeypatch):
    provider = AnthropicProvider(api_key="fake")

    class _FakeResponse:
        content = []

    class _FakeMessages:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeClient:
        messages = _FakeMessages()

    monkeypatch.setattr(provider, "_client", lambda: _FakeClient())
    with pytest.raises(ValueError):
        provider.analyze("claude-sonnet-5", "log line", 0.2)
