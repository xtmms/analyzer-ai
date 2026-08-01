def test_register_creates_user(client):
    resp = client.post(
        "/auth/register", json={"email": "new-user@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new-user@example.com"
    assert body["plan"] == "free"
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "wrongpw@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "wrongpw@example.com", "password": "nope12345"})
    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post("/auth/login", json={"email": "ghost@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_rejects_invalid_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers, email = auth_headers
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == email
