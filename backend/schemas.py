"""Pydantic request/response models."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    phone: str = Field(min_length=6, max_length=20)
    display_name: str = Field(default="", max_length=80)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        return v.strip().lower()


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    phone: str
    display_name: str
    is_admin: bool
    created_at: str


class AlertCreate(BaseModel):
    category: str = Field(max_length=40)
    severity: str = Field(max_length=20)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    lat: float | None = None
    lng: float | None = None


class AlertUpdate(BaseModel):
    status: str  # 'active' | 'resolved'


class AlertOut(BaseModel):
    id: int
    author_id: int
    author_name: str
    category: str
    severity: str
    title: str
    description: str
    lat: float | None
    lng: float | None
    status: str
    created_at: str
    updated_at: str


class CheckInCreate(BaseModel):
    note: str = Field(default="", max_length=500)
    lat: float | None = None
    lng: float | None = None


class CheckInOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    note: str
    lat: float | None
    lng: float | None
    created_at: str
