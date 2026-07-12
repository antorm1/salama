"""Salama Community Safety — FastAPI backend.

Offline-first safety app: SOS alerts, local hazard map, neighbor check-ins.
Run with:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

import database
import security
from config import settings
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

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

ALLOWED_CATEGORIES = {"sos", "hazard", "medical", "weather", "crime", "other"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_STATUSES = {"active", "resolved"}


# --------------------------------------------------------------------------- #
# Dependency helpers
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = security.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    with database.db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),)).fetchone()
    if not row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return dict(row)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user["is_admin"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return user


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister):
    username = payload.username
    phone = security.normalize_phone(payload.phone)
    if not phone:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A valid phone number is required")
    with database.db_session() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already registered")
        cur = conn.execute(
            """
            INSERT INTO users (username, phone, display_name, hashed_password, is_admin, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (username, phone, payload.display_name or username, security.hash_password(payload.password), now_iso()),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _user_out(dict(row))


@app.post("/auth/token", response_model=Token)
def login(payload: UserLogin):
    with database.db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username.lower(),)).fetchone()
    if not row or not security.verify_password(payload.password, row["hashed_password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    token = security.create_access_token(row["id"], bool(row["is_admin"]))
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return _user_out(user)


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
@app.post("/alerts", response_model=AlertOut, status_code=201)
def create_alert(payload: AlertCreate, user: dict = Depends(get_current_user)):
    cat = (payload.category or "other").lower()
    sev = (payload.severity or "medium").lower()
    if cat not in ALLOWED_CATEGORIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"category must be one of {sorted(ALLOWED_CATEGORIES)}")
    if sev not in ALLOWED_SEVERITIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"severity must be one of {sorted(ALLOWED_SEVERITIES)}")
    ts = now_iso()
    with database.db_session() as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts (author_id, category, severity, title, description, lat, lng, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (user["id"], cat, sev, payload.title.strip(), payload.description, payload.lat, payload.lng, ts, ts),
        )
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cur.lastrowid,)).fetchone()
        author = conn.execute("SELECT display_name, username FROM users WHERE id = ?", (user["id"],)).fetchone()
    return _alert_out(dict(row), author)


@app.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status_filter: str = Query("active", alias="status"),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    if status_filter not in (ALLOWED_STATUSES | {"all"}):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be active|resolved|all")
    clauses = []
    params: list = []
    if status_filter != "all":
        clauses.append("a.status = ?")
        params.append(status_filter)
    if category:
        clauses.append("a.category = ?")
        params.append(category.lower())
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT a.*, u.display_name AS author_name
        FROM alerts a JOIN users u ON u.id = a.author_id
        {where}
        ORDER BY a.created_at DESC
        LIMIT ?
    """
    params.append(limit)
    with database.db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_alert_out(dict(r), None) for r in rows]


@app.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, user: dict = Depends(get_current_user)):
    with database.db_session() as conn:
        row = conn.execute(
            "SELECT a.*, u.display_name AS author_name FROM alerts a JOIN users u ON u.id=a.author_id WHERE a.id = ?",
            (alert_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return _alert_out(dict(row), None)


@app.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, payload: AlertUpdate, user: dict = Depends(get_current_user)):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be active|resolved")
    with database.db_session() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
        if not user["is_admin"] and row["author_id"] != user["id"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to update this alert")
        conn.execute(
            "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
            (payload.status, now_iso(), alert_id),
        )
        row = conn.execute(
            "SELECT a.*, u.display_name AS author_name FROM alerts a JOIN users u ON u.id=a.author_id WHERE a.id = ?",
            (alert_id,),
        ).fetchone()
        author = conn.execute("SELECT display_name FROM users WHERE id = ?", (row["author_id"],)).fetchone()
    return _alert_out(dict(row), author)


@app.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int, user: dict = Depends(require_admin)):
    with database.db_session() as conn:
        res = conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        if res.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")


# --------------------------------------------------------------------------- #
# Check-ins
# --------------------------------------------------------------------------- #
@app.post("/checkins", response_model=CheckInOut, status_code=201)
def create_checkin(payload: CheckInCreate, user: dict = Depends(get_current_user)):
    ts = now_iso()
    with database.db_session() as conn:
        cur = conn.execute(
            """
            INSERT INTO checkins (user_id, note, lat, lng, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], payload.note, payload.lat, payload.lng, ts),
        )
        row = conn.execute("SELECT * FROM checkins WHERE id = ?", (cur.lastrowid,)).fetchone()
        author = conn.execute("SELECT display_name, username FROM users WHERE id = ?", (user["id"],)).fetchone()
    return _checkin_out(dict(row), author)


@app.get("/checkins", response_model=list[CheckInOut])
def list_checkins(
    limit: int = Query(100, ge=1, le=500),
    only_mine: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    if only_mine:
        params: list = [user["id"], limit]
        where = "WHERE c.user_id = ?"
    else:
        params = [limit]
        where = ""
    sql = f"""
        SELECT c.*, u.display_name AS user_name
        FROM checkins c JOIN users u ON u.id = c.user_id
        {where}
        ORDER BY c.created_at DESC
        LIMIT ?
    """
    with database.db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_checkin_out(dict(r), None) for r in rows]


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "time": now_iso()}


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def _user_out(row: dict) -> UserOut:
    return UserOut(
        id=row["id"],
        username=row["username"],
        phone=row["phone"],
        display_name=row["display_name"],
        is_admin=bool(row["is_admin"]),
        created_at=row["created_at"],
    )


def _alert_out(row: dict, author: sqlite3.Row | None) -> AlertOut:
    name = row.get("author_name") or (author["display_name"] if author else "unknown")
    return AlertOut(
        id=row["id"],
        author_id=row["author_id"],
        author_name=name,
        category=row["category"],
        severity=row["severity"],
        title=row["title"],
        description=row["description"],
        lat=row["lat"],
        lng=row["lng"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _checkin_out(row: dict, author: sqlite3.Row | None) -> CheckInOut:
    name = row.get("user_name") or (author["display_name"] if author else "unknown")
    return CheckInOut(
        id=row["id"],
        user_id=row["user_id"],
        user_name=name,
        note=row["note"],
        lat=row["lat"],
        lng=row["lng"],
        created_at=row["created_at"],
    )


# --------------------------------------------------------------------------- #
# Startup
# --------------------------------------------------------------------------- #
@app.on_event("startup")
def _startup():
    database.init_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
