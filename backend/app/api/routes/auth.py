from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database.session import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    AutoLoginResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/auth/login", auto_error=False
)

DEFAULT_PREFERENCES = {
    "provider_ia": "fallback",
    "api_key": "",
    "theme": "dark",
    "font_size": 14,
    "terminal_type": "simulation",
}

DEFAULT_STATS = {
    "total_time": 0,
    "levels_completed": 0,
    "points": 0,
    "rank": "Novice",
    "badges": [],
}


def get_password_hash(password: str) -> str:
    # bcrypt only uses the first 72 bytes; truncate to avoid errors on longer input.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Returns the username encoded in a valid token, or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        return username if username else None
    except JWTError:
        return None


def create_default_user_if_not_exists(db: Session) -> Optional[User]:
    """Creates the bootstrap admin on first run (zero-config setup)."""
    if not settings.BOOTSTRAP_ADMIN:
        return None
    user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if not user:
        user = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            preferences=dict(DEFAULT_PREFERENCES),
            stats=dict(DEFAULT_STATS),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise. Veuillez vous connecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    username = decode_token(token)
    if not username:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")
    db_email = db.query(User).filter(User.email == user_in.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        preferences=dict(DEFAULT_PREFERENCES),
        stats=dict(DEFAULT_STATS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    create_default_user_if_not_exists(db)

    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auto", response_model=AutoLoginResponse)
def auto_login(db: Session = Depends(get_db)):
    """Zero-login session for a private/internal instance.

    Ensures the bootstrap admin exists and issues a token for it, so the
    frontend can land directly on the dashboard without a login page.
    """
    admin = create_default_user_if_not_exists(db)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucun compte disponible pour l'accès automatique.",
        )

    access_token = create_access_token(data={"sub": admin.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": admin,
    }
