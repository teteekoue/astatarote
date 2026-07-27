from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserPreferences(BaseModel):
    provider_ia: str = "fallback"  # fallback, nvidia, groq, fireworks, cohere, together
    api_key: Optional[str] = None
    theme: str = "dark"
    font_size: int = 14
    terminal_type: str = "simulation" # simulation, docker, reel

class UserResponse(UserBase):
    id: int
    preferences: UserPreferences
    stats: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Game Schemas
class GameCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    domain: str = "linux"  # linux, network, security
    level: str = "beginner"  # beginner, intermediate, advanced
    custom_prompt: Optional[str] = None

class GameResponse(BaseModel):
    id: int
    user_id: int
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

# Level Schemas
class ScenarioConfig(BaseModel):
    type: str = "simulation" # simulation, docker, reel
    initial_state: Dict[str, Any] = {}
    expected_state: Dict[str, Any] = {}
    commands_allowed: List[str] = []
    forbidden_commands: List[str] = []

class LevelResponse(BaseModel):
    id: int
    game_id: int
    level_index: int
    title: str
    description: str
    objective: str
    
    # New fields for high inspiration
    situation_probleme: Optional[str] = None
    consigne: Optional[str] = None
    support_technique: Optional[str] = None

    scenario: Dict[str, Any]
    hints: List[str]
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

# Chat Schemas
class ChatMessage(BaseModel):
    sender: str  # "user" or "ai"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatHistory(BaseModel):
    history: List[ChatMessage]
