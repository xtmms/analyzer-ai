"""
Test delle route di parsing/stima/analisi. Il provider AI è sempre mockato
(_FakeProvider): niente chiamate di rete reali, coerente con la convenzione
"i test girano senza chiave API e senza rete" già in AGENTS.md per core/.
"""
from core.report_schema import LogAnalysisReport, ReportPoint

LOG_CONTENT = (
    "2026-01-01 10:00:00 ERROR something broke\n"
    "2026-01-01 10:00:01 INFO all good\n"
    "2026-01-01 10:00:02 WARNING careful\n"
)


class _FakeSettings:
    def __init__(self, max_upload_chars=5_000_000, provider_keys=None):
        self.max_upload_chars = max_upload_chars
        self.provider_keys = provider_keys or {
            "gemini": "fake-key",
            "openai": None,
            "anthropic": None,
        }


class _FakeProvider:
    def count_tokens(self, model, text):
        return 42, True

    def analyze(self, model, logs_payload, temperature):
        return LogAnalysisReport(
            problem_summary=ReportPoint(title="Sintesi", content="c1"),
            root_cause_analysis=ReportPoint(title="Causa", content="c2"),
            recommendations=ReportPoint(title="Fix", content="c3"),
        )


def _patch_provider(monkeypatch, settings=None):
    monkeypatch.setattr("backend.app.routes.logs.get_settings", lambda: settings or _FakeSettings())
    monkeypatch.setattr(
        "backend.app.routes.logs.build_provider", lambda provider_id, api_key: _FakeProvider()
    )


# --- /logs/parse -------------------------------------------------------------


def test_parse_logs_requires_auth(client):
    resp = client.post("/logs/parse", json={"log_content": "x", "severities": []})
    assert resp.status_code == 401


def test_parse_logs_filters_and_counts(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/logs/parse",
        headers=headers,
        json={"log_content": LOG_CONTENT, "severities": ["ERROR", "WARNING", "CRITICAL"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_lines"] == 3
    assert body["filtered_count"] == 2
    assert body["severity_counts"]["ERROR"] == 1
    assert body["severity_counts"]["INFO"] == 1


# --- /logs/estimate ------------------------------------------------------------


def test_estimate_rejects_unconfigured_provider(client, auth_headers):
    headers, _ = auth_headers
    resp = client.post(
        "/logs/estimate",
        headers=headers,
        json={"provider": "openai", "model": "gpt-4.1-mini", "logs_payload": "log line"},
    )
    assert resp.status_code == 400


def test_estimate_returns_cost_breakdown_with_mocked_provider(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    _patch_provider(monkeypatch)
    resp = client.post(
        "/logs/estimate",
        headers=headers,
        json={"provider": "gemini", "model": "gemini-2.5-flash", "logs_payload": "log line"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_count"] == 42
    assert body["is_real_token_count"] is True
    assert body["cost_breakdown"]["total_cost"] > 0


# --- /logs/analyze + storico + quota --------------------------------------------


def test_analyze_persists_record_and_increments_usage(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    _patch_provider(monkeypatch)

    resp = client.post(
        "/logs/analyze",
        headers=headers,
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "logs_payload": "ERROR broke",
            "filename": "sample.log",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["report"]["problem_summary"]["title"] == "Sintesi"

    usage = client.get("/usage/me", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["used"] == 1

    history = client.get("/analyses", headers=headers)
    assert history.status_code == 200
    records = history.json()
    assert len(records) == 1
    assert records[0]["filename"] == "sample.log"

    detail = client.get(f"/analyses/{records[0]['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["report_json"]["recommendations"]["content"] == "c3"


def test_analyze_blocked_once_quota_exhausted(client, auth_headers, monkeypatch):
    headers, _ = auth_headers
    _patch_provider(monkeypatch)
    monkeypatch.setattr(
        "backend.app.quota.get_settings",
        lambda: type("S", (), {"free_plan_monthly_limit": 1, "pro_plan_monthly_limit": 500})(),
    )

    payload = {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "logs_payload": "ERROR broke",
        "filename": "sample.log",
    }

    first = client.post("/logs/analyze", headers=headers, json=payload)
    assert first.status_code == 200

    second = client.post("/logs/analyze", headers=headers, json=payload)
    assert second.status_code == 403
    assert "quota" in second.json()["detail"].lower()


def test_analyze_requires_auth(client):
    resp = client.post(
        "/logs/analyze",
        json={"provider": "gemini", "model": "gemini-2.5-flash", "logs_payload": "x"},
    )
    assert resp.status_code == 401


def test_analysis_detail_not_found_for_other_users(client, auth_headers, monkeypatch):
    headers, owner_email = auth_headers
    _patch_provider(monkeypatch)
    client.post(
        "/logs/analyze",
        headers=headers,
        json={
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "logs_payload": "ERROR broke",
            "filename": "sample.log",
        },
    )
    owned_record_id = client.get("/analyses", headers=headers).json()[0]["id"]

    other_headers, _ = _register_and_login(client, "other-user@example.com")
    resp = client.get(f"/analyses/{owned_record_id}", headers=other_headers)
    assert resp.status_code == 404


def _register_and_login(client, email: str):
    password = "password123"
    client.post("/auth/register", json={"email": email, "password": password})
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email
