from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import models, quota, schemas
from backend.app.auth import get_current_user
from backend.app.db import get_db

router = APIRouter()


@router.get("/me", response_model=schemas.UsageOut)
def usage_me(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return quota.get_usage_status(db, current_user)
