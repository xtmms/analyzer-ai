"""
Entrypoint FastAPI. Avviare da root repo con:
    uvicorn backend.app.main:app --reload
così core/ e config.py restano importabili senza hack di path (stesso
principio già usato da conftest.py per i test).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.db import init_db
from backend.app.rate_limit import limiter
from backend.app.routes import auth as auth_routes
from backend.app.routes import history as history_routes
from backend.app.routes import logs as logs_routes
from backend.app.routes import providers as providers_routes
from backend.app.routes import usage as usage_routes
from backend.app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ai_log_analyzer")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Log Analyzer API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Non lasciamo mai trapelare stacktrace/dettagli interni al client."""
    logger.exception("Errore interno non gestito su %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Si è verificato un errore interno. Riprova più tardi."},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(providers_routes.router, prefix="/providers", tags=["providers"])
app.include_router(logs_routes.router, prefix="/logs", tags=["logs"])
app.include_router(history_routes.router, prefix="/analyses", tags=["history"])
app.include_router(usage_routes.router, prefix="/usage", tags=["usage"])
