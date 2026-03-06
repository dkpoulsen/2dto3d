"""Database models for user authentication.

This module defines SQLAlchemy models for user storage
and database initialization functions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from video2d3d.utils.logger import get_logger

logger = get_logger("web.auth.database")


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class UserModel(Base):
    """SQLAlchemy model for user storage."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username={self.username}, role={self.role})>"


# Global database engine and session factory
_engine = None
_session_factory = None


def get_database_path() -> Path:
    """Get the path to the SQLite database file."""
    # Store in the same directory as other app data
    from video2d3d.web.state import app_state

    data_dir = app_state.upload_dir.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "auth.db"


def init_database(db_path: Optional[Path] = None) -> None:
    """Initialize the database engine and create tables.

    Args:
        db_path: Optional path to the database file.
                 If not provided, uses default location.
    """
    global _engine, _session_factory

    if db_path is None:
        db_path = get_database_path()

    # Create engine
    db_url = f"sqlite:///{db_path}"
    _engine = create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},  # SQLite specific
    )

    # Create tables
    Base.metadata.create_all(_engine)

    # Create session factory
    _session_factory = sessionmaker(bind=_engine)

    logger.info(f"Database initialized at {db_path}")


def get_session() -> Session:
    """Get a database session.

    Returns:
        SQLAlchemy Session instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _session_factory is None:
        init_database()
    return _session_factory()


def get_engine():
    """Get the database engine.

    Returns:
        SQLAlchemy Engine instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _engine is None:
        init_database()
    return _engine


__all__ = [
    "Base",
    "UserModel",
    "init_database",
    "get_session",
    "get_engine",
    "get_database_path",
]
