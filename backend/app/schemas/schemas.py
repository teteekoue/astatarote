from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

# ---------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserPreferences(BaseModel):
    provider_ia: str = "fallback"  # fallback, nvidia, groq, fireworks, cohere, together
    api_key: Optional[str] = None
    theme: str = "dark"
    font_size: int = 14
    terminal_type: str = "simulation"  # simulation, docker, reel


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


def mask_api_key(key: Optional[str]) -> Optional[str]:
    """Mask a secret API key for safe responses."""
    if not key:
        return None
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}{'•' * (len(key) - 8)}{key[-4:]}"


class UserResponse(UserBase):
    id: int
    preferences: Dict[str, Any]
    stats: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("preferences", mode="before")
    @classmethod
    def mask_api_key_in_preferences(cls, v: Any) -> Any:
        if isinstance(v, dict) and v.get("api_key"):
            v = dict(v)
            v["api_key"] = mask_api_key(v["api_key"])
        return v


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AutoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


# ---------------------------------------------------------------
# Game Schemas
# ---------------------------------------------------------------

class GameStart(BaseModel):
    """Start (enroll into) a frozen catalog course."""
    catalog_slug: str = Field(min_length=1, max_length=80)


class GameResponse(BaseModel):
    id: int
    user_id: int
    catalog_slug: Optional[str] = None
    name: str
    description: Optional[str]
    domain: str
    level: str
    status: str
    current_level_index: int
    total_levels: int
    progress: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CatalogGameResponse(BaseModel):
    slug: str
    name: str
    tagline: str
    description: str
    domain: str
    level: str
    difficulty: int
    duration_minutes: int
    skills: List[str]
    version: str
    total_levels: int
    total_points: int
    enrolled: bool = False
    enrollment: Optional[GameResponse] = None


# ---------------------------------------------------------------
# Level Schemas
# ---------------------------------------------------------------

class LevelResponse(BaseModel):
    id: int
    game_id: int
    level_index: int
    title: str
    description: str
    objective: str
    situation_probleme: Optional[str] = None
    consigne: Optional[str] = None
    support_technique: Optional[str] = None
    scenario: Dict[str, Any]
    hints: List[str] = []
    difficulty: int
    points: int
    time_limit: int
    status: str
    attempts: int
    time_spent: int
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Level Validation
class ValidateResponse(BaseModel):
    success: bool
    message: str
    points_earned: int = 0
    badge_unlocked: Optional[str] = None
    next_level_index: Optional[int] = None


# ---------------------------------------------------------------
# Chat Schemas
# ---------------------------------------------------------------

class ChatMessage(BaseModel):
    sender: str  # "user" or "ai"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
