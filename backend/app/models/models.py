from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    preferences = Column(JSON, default=dict)  # provider_ia, api_key, theme, font_size, terminal_type
    stats = Column(JSON, default=dict)        # total_time, levels_completed, points, rank, badges
    created_at = Column(DateTime, default=datetime.utcnow)

    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=False)       # "linux", "network", "security"
    level = Column(String, nullable=False)        # "beginner", "intermediate", "advanced"
    status = Column(String, default="active")     # "active", "completed"
    current_level_index = Column(Integer, default=0)
    total_levels = Column(Integer, default=5)
    progress = Column(Float, default=0.0)         # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="games")
    levels = relationship("Level", back_populates="game", cascade="all, delete-orphan")
    game_states = relationship("GameState", back_populates="game", cascade="all, delete-orphan")

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    level_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    objective = Column(Text, nullable=False)
    scenario = Column(JSON, default=dict)         # initial_state, expected_state, commands_allowed, etc.
    hints = Column(JSON, default=list)            # list of hints
    difficulty = Column(Integer, default=1)       # 1-10
    points = Column(Integer, default=100)
    time_limit = Column(Integer, default=600)     # seconds
    status = Column(String, default="locked")     # "locked", "available", "in_progress", "completed"
    attempts = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)       # seconds
    completed_at = Column(DateTime, nullable=True)

    game = relationship("Game", back_populates="levels")
    game_states = relationship("GameState", back_populates="level", cascade="all, delete-orphan")

class GameState(Base):
    __tablename__ = "game_states"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)
    terminal_state = Column(JSON, default=dict)   # current_directory, files, variables, processes
    chat_history = Column(JSON, default=list)     # chat dialogue list
    memory_summary = Column(Text, default="{}")   # JSON summary of skills / progress
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game", back_populates="game_states")
    level = relationship("Level", back_populates="game_states")
