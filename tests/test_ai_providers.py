"""
Test del modulo core/ai_providers/ adattati per la versione CLI (solo Gemini).
"""
import pytest

from core.ai_providers.gemini_provider import GeminiProvider
from core.ai_providers.registry import (
    build_provider,
    calculate_cost,
    get_provider_class,
)
from core.report_schema import LogAnalysisReport, ReportPoint

def _sample_report() -> LogAnalysisReport:
    return LogAnalysisReport(
        problem_summary=ReportPoint(title="t1", content="c1"),
        root_cause_analysis=ReportPoint(title="t2", content="c2"),
        recommendations=ReportPoint(title="t3", content="c3"),
    )

# --- registry.py -------------------------------------------------------------

def test_get_provider_class_known_ids():
    assert get_provider_class("gemini") is GeminiProvider

def test_get_provider_class_unknown_raises():
    with pytest.raises(ValueError):
        get_provider_class("does-not-exist")

def test_build_provider_sets_api_key():
    provider = build_provider("gemini", "fake-key")
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "fake-key"

def test_calculate_cost():
    cost = calculate_cost("gemini", "gemini-3.6-flash", 1_000_000, 1_000_000)
    assert cost["input_cost"] == 0.075
    assert cost["output_cost"] == 0.30
    assert cost["total_cost"] == 0.375

# --- gemini_provider.py ------------------------------------------------------

def test_gemini_provider_analyze_returns_parsed_report_and_usage(monkeypatch):
    provider = GeminiProvider(api_key="fake")
    fake_report = _sample_report()

    class _FakeUsage:
        prompt_token_count = 10
        candidates_token_count = 20
        total_token_count = 30

    class _FakeResponse:
        parsed = fake_report
        text = ""
        usage_metadata = _FakeUsage()

    class _FakeChat:
        def send_message(self, *args, **kwargs):
            return _FakeResponse()

    class _FakeChats:
        def create(self, **kwargs):
            return _FakeChat()

    class _FakeClient:
        chats = _FakeChats()

    monkeypatch.setattr(provider, "_client", lambda: _FakeClient())
    result, usage = provider.analyze("gemini-3.6-flash", "log line", 0.0, "Dettagliato")
    assert result == fake_report
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 20
    assert usage["total_tokens"] == 30
