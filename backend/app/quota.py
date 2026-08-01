"""
Limiti mensili per piano (free/pro). Nessun collegamento a un vero
processore di pagamenti in questa fase: il campo User.plan viene aggiornato
manualmente (o da un futuro endpoint admin) — vedi AGENTS.md/README per la
nota su Stripe non integrato.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.settings import get_settings


def _plan_limits() -> dict[str, int]:
    settings = get_settings()
    return {
        "free": settings.free_plan_monthly_limit,
        "pro": settings.pro_plan_monthly_limit,
    }


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_or_create_usage_counter(db: Session, user: models.User, period: str) -> models.UsageCounter:
    counter = (
        db.query(models.UsageCounter).filter_by(user_id=user.id, period=period).one_or_none()
    )
    if counter is None:
        counter = models.UsageCounter(user_id=user.id, period=period, analyses_count=0)
        db.add(counter)
        db.flush()
    return counter


def get_usage_status(db: Session, user: models.User) -> dict:
    period = current_period()
    counter = get_or_create_usage_counter(db, user, period)
    limit = _plan_limits().get(user.plan, _plan_limits()["free"])
    return {
        "plan": user.plan,
        "period": period,
        "used": counter.analyses_count,
        "limit": limit,
        "remaining": max(0, limit - counter.analyses_count),
    }


def enforce_quota_or_raise(db: Session, user: models.User) -> models.UsageCounter:
    period = current_period()
    counter = get_or_create_usage_counter(db, user, period)
    limit = _plan_limits().get(user.plan, _plan_limits()["free"])
    if counter.analyses_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Quota mensile del piano '{user.plan}' esaurita ({limit} analisi/mese). "
                "Effettua l'upgrade per continuare."
            ),
        )
    return counter


def record_usage(counter: models.UsageCounter) -> None:
    counter.analyses_count += 1
