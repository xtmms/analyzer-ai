"""
Fixture condivise per i test del backend: DB SQLite temporaneo isolato,
nessuna chiave provider reale (le variabili d'ambiente esplicite vincono
sempre sul file .env di root — vedi precedenza di pydantic-settings), così
i test non toccano mai rete o account reali. I singoli test che devono
simulare un provider "configurato" monkeypatchano get_settings/build_provider
nel modulo sotto test, non le variabili d'ambiente globali.
"""
import atexit
import os
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
atexit.register(lambda: Path(_tmp_db_path).unlink(missing_ok=True))

os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["CORS_ORIGINS_RAW"] = "http://localhost:5173"
os.environ["FREE_PLAN_MONTHLY_LIMIT"] = "10"
os.environ["PRO_PLAN_MONTHLY_LIMIT"] = "500"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    """Registra e logga un utente nuovo (email casuale) e ritorna gli
    header Authorization pronti per l'uso, oltre all'email usata."""
    import uuid

    email = f"user-{uuid.uuid4().hex}@example.com"
    password = "password123"

    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}, email
