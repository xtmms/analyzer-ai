"""
Route di parsing/filtraggio, stima costi e analisi AI. Tutta la logica di
dominio vive in core/ (log_parser, formatting, ai_providers) e in
core/ai_providers/registry.py: qui si orchestrano solo request/response,
autenticazione, quota e persistenza.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app import models, quota, schemas
from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.rate_limit import limiter
from backend.app.settings import get_settings
from config import SEVERITY_LEVELS
from core.ai_providers.base import AIProvider
from core.ai_providers.registry import build_provider, estimate_cost, suggest_cheaper_model
from core.formatting import colorize_log
from core.log_parser import filter_entries, parse_log_to_entries, prepare_entries_for_send

router = APIRouter()


def _get_provider_or_400(provider_id: str) -> AIProvider:
    settings = get_settings()
    api_key = settings.provider_keys.get(provider_id)
    if not api_key:
        raise HTTPException(
            status_code=400, detail=f"Provider '{provider_id}' non configurato lato server."
        )
    return build_provider(provider_id, api_key)


@router.post("/parse", response_model=schemas.ParseLogsOut)
def parse_logs(
    payload: schemas.ParseLogsIn, current_user: models.User = Depends(get_current_user)
) -> schemas.ParseLogsOut:
    settings = get_settings()
    if len(payload.log_content) > settings.max_upload_chars:
        raise HTTPException(status_code=413, detail="File di log troppo grande.")

    entries = parse_log_to_entries(payload.log_content)
    total_lines = len(entries)

    severity_counts = {level: 0 for level in SEVERITY_LEVELS}
    for entry in entries:
        if entry["severity"] in severity_counts:
            severity_counts[entry["severity"]] += 1

    filtered = filter_entries(entries, payload.severities, payload.search_query)
    filtered_count = len(filtered)

    max_lines = max(1, payload.max_lines)
    ordered = filtered[-max_lines:] if payload.slice_from_end else filtered[:max_lines]
    logs_to_send = prepare_entries_for_send(ordered, dedupe=payload.dedupe)
    preview_text = "\n".join(logs_to_send)

    return schemas.ParseLogsOut(
        total_lines=total_lines,
        filtered_count=filtered_count,
        severity_counts=severity_counts,
        logs_to_send=logs_to_send,
        colorized_preview=colorize_log(preview_text),
    )


@router.post("/estimate", response_model=schemas.EstimateOut)
def estimate_logs(
    payload: schemas.AnalyzeLogsIn, current_user: models.User = Depends(get_current_user)
) -> schemas.EstimateOut:
    provider = _get_provider_or_400(payload.provider)
    token_count, is_real = provider.count_tokens(payload.model, payload.logs_payload)
    return schemas.EstimateOut(
        token_count=token_count,
        is_real_token_count=is_real,
        cost_breakdown=estimate_cost(token_count, payload.provider, payload.model),
        suggestion=suggest_cheaper_model(token_count, payload.provider, payload.model),
    )


@router.post("/analyze", response_model=schemas.AnalyzeLogsOut)
@limiter.limit(get_settings().rate_limit_analyze)
def analyze_logs_endpoint(
    request: Request,
    payload: schemas.AnalyzeLogsIn,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.AnalyzeLogsOut:
    settings = get_settings()
    if len(payload.logs_payload) > settings.max_upload_chars:
        raise HTTPException(status_code=413, detail="Payload di log troppo grande.")

    counter = quota.enforce_quota_or_raise(db, current_user)
    provider = _get_provider_or_400(payload.provider)

    token_count, is_real = provider.count_tokens(payload.model, payload.logs_payload)
    cost_breakdown = estimate_cost(token_count, payload.provider, payload.model)

    try:
        report = provider.analyze(payload.model, payload.logs_payload, payload.temperature)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Errore dal provider AI: {exc}") from exc

    quota.record_usage(counter)
    db.add(
        models.AnalysisRecord(
            user_id=current_user.id,
            filename=payload.filename,
            provider=payload.provider,
            model_used=payload.model,
            token_count=token_count,
            cost_estimate=cost_breakdown["total_cost"],
            report_json=report.model_dump(),
        )
    )
    db.commit()

    return schemas.AnalyzeLogsOut(
        token_count=token_count,
        is_real_token_count=is_real,
        cost_breakdown=cost_breakdown,
        suggestion=suggest_cheaper_model(token_count, payload.provider, payload.model),
        report=report.model_dump(),
    )
