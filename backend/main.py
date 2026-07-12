"""Salama Community Safety — FastAPI backend.

Offline-first safety app: SOS alerts, local hazard map, neighbor check-ins.
Database is driven by DATABASE_URL (SQLite by default, PostgreSQL in prod).
Run with:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

import database
import security
from config import settings
from database import Alert, CheckIn, User
from schemas import (
    AlertCreate,
    AlertOut,
    AlertUpdate,
    CheckInCreate,
    CheckInOut,
    Token,
    UserLogin,
    UserOut,
    UserRegister,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

ALLOWED_CATEGORIES = {"sos", "hazard", "medical", "weather", "crime", "other"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_STATUSES = {"active", "resolved"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Dependency helpers
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> User:
    payload = security.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return user


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(database.get_db)):
    username = payload.username.strip().lower()
    phone = security.normalize_phone(payload.phone)
    if not phone:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A valid phone number is required")
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already registered")
    user = User(
        username=username,
        phone=phone,
        display_name=payload.display_name or username,
        hashed_password=security.hash_password(payload.password),
        is_admin=False,
        created_at=now_iso(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@app.post("/auth/token", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(database.get_db)):
    user = db.scalar(select(User).where(User.username == payload.username.strip().lower()))
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    token = security.create_access_token(user.id, bool(user.is_admin))
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
@app.post("/alerts", response_model=AlertOut, status_code=201)
def create_alert(payload: AlertCreate, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    cat = (payload.category or "other").lower()
    sev = (payload.severity or "medium").lower()
    if cat not in ALLOWED_CATEGORIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"category must be one of {sorted(ALLOWED_CATEGORIES)}")
    if sev not in ALLOWED_SEVERITIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"severity must be one of {sorted(ALLOWED_SEVERITIES)}")
    ts = now_iso()
    alert = Alert(
        author_id=user.id,
        category=cat,
        severity=sev,
        title=payload.title.strip(),
        description=payload.description,
        lat=payload.lat,
        lng=payload.lng,
        status="active",
        created_at=ts,
        updated_at=ts,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _alert_out(alert)


@app.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status_filter: str = Query("active", alias="status"),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    if status_filter not in (ALLOWED_STATUSES | {"all"}):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be active|resolved|all")
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if status_filter != "all":
        stmt = stmt.where(Alert.status == status_filter)
    if category:
        stmt = stmt.where(Alert.category == category.lower())
    stmt = stmt.limit(limit)
    alerts = db.scalars(stmt).all()
    return [_alert_out(a) for a in alerts]


@app.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return _alert_out(alert)


@app.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, payload: AlertUpdate, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be active|resolved")
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    if not user.is_admin and alert.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to update this alert")
    alert.status = payload.status
    alert.updated_at = now_iso()
    db.commit()
    db.refresh(alert)
    return _alert_out(alert)


@app.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int, user: User = Depends(require_admin), db: Session = Depends(database.get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    db.delete(alert)
    db.commit()


# --------------------------------------------------------------------------- #
# Check-ins
# --------------------------------------------------------------------------- #
@app.post("/checkins", response_model=CheckInOut, status_code=201)
def create_checkin(payload: CheckInCreate, user: User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    ci = CheckIn(
        user_id=user.id,
        note=payload.note,
        lat=payload.lat,
        lng=payload.lng,
        created_at=now_iso(),
    )
    db.add(ci)
    db.commit()
    db.refresh(ci)
    return _checkin_out(ci)


@app.get("/checkins", response_model=list[CheckInOut])
def list_checkins(
    limit: int = Query(100, ge=1, le=500),
    only_mine: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    stmt = select(CheckIn).order_by(CheckIn.created_at.desc())
    if only_mine:
        stmt = stmt.where(CheckIn.user_id == user.id)
    stmt = stmt.limit(limit)
    items = db.scalars(stmt).all()
    return [_checkin_out(c) for c in items]


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "time": now_iso()}


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def _user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        phone=u.phone,
        display_name=u.display_name,
        is_admin=bool(u.is_admin),
        created_at=u.created_at,
    )


def _alert_out(a: Alert) -> AlertOut:
    return AlertOut(
        id=a.id,
        author_id=a.author_id,
        author_name=a.author.display_name if a.author else "unknown",
        category=a.category,
        severity=a.severity,
        title=a.title,
        description=a.description,
        lat=a.lat,
        lng=a.lng,
        status=a.status,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _checkin_out(c: CheckIn) -> CheckInOut:
    return CheckInOut(
        id=c.id,
        user_id=c.user_id,
        user_name=c.user.display_name if c.user else "unknown",
        note=c.note,
        lat=c.lat,
        lng=c.lng,
        created_at=c.created_at,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
