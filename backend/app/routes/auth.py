from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth import create_access_token, get_current_user, hash_password, verify_password
from backend.app.db import get_db

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)) -> models.User:
    existing = db.query(models.User).filter_by(email=payload.email).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Un account con questa email esiste già.")

    user = models.User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)) -> schemas.TokenOut:
    user = db.query(models.User).filter_by(email=payload.email).one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o password non corrette.")
    token = create_access_token(subject=str(user.id))
    return schemas.TokenOut(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user
