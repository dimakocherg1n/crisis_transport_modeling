# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Имя пользователя должно быть не менее 3 символов')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры и подчеркивания')
        return v
class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен быть не менее 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v
class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
class UserInDB(UserBase):
    """Схема пользователя в базе данных"""
    id: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True
class UserResponse(UserInDB):
    """Схема ответа с пользователем"""
    pass
class Token(BaseModel):
    """Схема токена"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
class TokenPayload(BaseModel):
    """Схема payload токена"""
    sub: str
    email: str
    role: str
    exp: int
class LoginRequest(BaseModel):
    """Схема для входа"""
    username: str
    password: str
class PasswordChangeRequest(BaseModel):
    """Схема для изменения пароля"""
    current_password: str
    new_password: str