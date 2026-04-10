from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("username")
    @classmethod
    def username_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username must not be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters long")
        return v

    @field_validator("email")
    @classmethod
    def email_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Email must not be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_must_match(cls, v: str, info: object) -> str:
        data = info.data if hasattr(info, "data") else {}
        password = data.get("password")
        if password is not None and v != password:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def email_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Email must not be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Password must not be empty")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Username must not be empty")
            if len(v) < 3:
                raise ValueError("Username must be at least 3 characters long")
            if len(v) > 50:
                raise ValueError("Username must be at most 50 characters long")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_must_match(cls, v: Optional[str], info: object) -> Optional[str]:
        data = info.data if hasattr(info, "data") else {}
        password = data.get("password")
        if password is not None and v != password:
            raise ValueError("Passwords do not match")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime