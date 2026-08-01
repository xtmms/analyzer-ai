from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth import get_current_user
from backend.app.db import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.AnalysisSummaryOut])
def list_analyses(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[models.AnalysisRecord]:
    return (
        db.query(models.AnalysisRecord)
        .filter_by(user_id=current_user.id)
        .order_by(desc(models.AnalysisRecord.created_at))
        .all()
    )


@router.get("/{analysis_id}", response_model=schemas.AnalysisDetailOut)
def get_analysis(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.AnalysisRecord:
    record = (
        db.query(models.AnalysisRecord)
        .filter_by(id=analysis_id, user_id=current_user.id)
        .one_or_none()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Analisi non trovata.")
    return record
