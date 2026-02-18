# app/crud/crud_user.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.database_models import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return db.query(User).filter(User.email == email).first()
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        return db.query(User).filter(User.username == username).first()
    def get_by_identifier(self, db: Session, *, identifier: str) -> Optional[User]:
        """Получить пользователя по email или username"""
        return db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Создать пользователя с хэшированием пароля"""
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    def authenticate(
            self, db: Session, *, identifier: str, password: str
    ) -> Optional[User]:
        """Аутентификация пользователя"""
        user = self.get_by_identifier(db, identifier=identifier)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    def update(
            self,
            db: Session,
            *,
            db_obj: User,
            obj_in: UserUpdate
    ) -> User:
        """Обновить пользователя (с обработкой пароля)"""
        update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    def is_active(self, user: User) -> bool:
        """Проверить активен ли пользователь"""
        return user.is_active
    def is_admin(self, user: User) -> bool:
        """Проверить является ли пользователь админом"""
        return user.role == "admin"
user = CRUDUser(User)