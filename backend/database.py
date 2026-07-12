"""Database engine, session, and ORM models.

Works with **both** SQLite (zero-config local dev) and PostgreSQL
(production). Driven entirely by DATABASE_URL:
  - sqlite:///./salama.db            -> local file (default)
  - postgresql+psycopg://user:pass@host:5432/salama  -> Postgres

All access goes through get_db() which yields a scoped session. Queries are
parameterized by the ORM, preventing SQL injection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=lambda: _now())

    alerts: Mapped[list["Alert"]] = relationship(back_populates="author")
    checkins: Mapped[list["CheckIn"]] = relationship(back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=lambda: _now())
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, default=lambda: _now())

    author: Mapped["User"] = relationship(back_populates="alerts")


class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False, default=lambda: _now())

    user: Mapped["User"] = relationship(back_populates="checkins")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_engine():
    url = settings.database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and seed an admin user if none exist."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(User).count() == 0:
            from security import hash_password

            db.add(
                User(
                    username=settings.seed_admin_username,
                    phone=settings.seed_admin_phone,
                    display_name="Salama Admin",
                    hashed_password=hash_password(settings.seed_admin_password),
                    is_admin=True,
                )
            )
            db.commit()


__all__ = ["Base", "User", "Alert", "CheckIn", "engine", "SessionLocal", "get_db", "init_db", "func"]
