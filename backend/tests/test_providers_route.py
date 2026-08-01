def test_list_providers_requires_auth(client):
    resp = client.get("/providers")
    assert resp.status_code == 401


def test_list_providers_empty_when_no_keys_configured(client, auth_headers):
    headers, _ = auth_headers
    resp = client.get("/providers", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_providers_returns_only_configured_ones(client, auth_headers, monkeypatch):
    headers, _ = auth_headers

    class _FakeSettings:
        provider_keys = {"gemini": "fake-key", "openai": None, "anthropic": ""}

    monkeypatch.setattr("backend.app.routes.providers.get_settings", lambda: _FakeSettings())

    resp = client.get("/providers", headers=headers)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert ids == ["gemini"]
