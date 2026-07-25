from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from backend.app.core.database.session import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "asta-secure-super-secret-key-for-jwt-tokens-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_default_user_if_not_exists(db: Session) -> User:
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        hashed_pw = get_password_hash("admin123")
        user = User(
            username="admin",
            email="admin@astarote.org",
            hashed_password=hashed_pw,
            preferences={
                "provider_ia": "fallback",
                "api_key": "",
                "theme": "dark",
                "font_size": 14,
                "terminal_type": "simulation"
            },
            stats={
                "total_time": 0,
                "levels_completed": 0,
                "points": 0,
                "rank": "Novice",
                "badges": []
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # If no token, auto-return or login the default user to ensure zero barriers to entry
    default_user = create_default_user_if_not_exists(db)
    if not token:
        return default_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        # Fallback gracefully to default user in local dev
        return default_user

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return default_user
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
        preferences={
            "provider_ia": "fallback",
            "api_key": "",
            "theme": "dark",
            "font_size": 14,
            "terminal_type": "simulation"
        },
        stats={
            "total_time": 0,
            "levels_completed": 0,
            "points": 0,
            "rank": "Novice",
            "badges": []
        }
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Automatically seed the admin user on login attempt as well
    create_default_user_if_not_exists(db)
    
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur ou mot de passe incorrect")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
