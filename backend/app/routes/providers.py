from fastapi import APIRouter, Depends

from backend.app import models, schemas
from backend.app.auth import get_current_user
from backend.app.settings import get_settings
from core.ai_providers.registry import list_available_providers

router = APIRouter()


@router.get("", response_model=list[schemas.ProviderOut])
def list_providers(current_user: models.User = Depends(get_current_user)) -> list[dict]:
    """Ritorna solo i provider per cui il backend ha una chiave configurata,
    così il frontend non propone mai una scelta destinata a fallire."""
    settings = get_settings()
    return list_available_providers(settings.provider_keys)
