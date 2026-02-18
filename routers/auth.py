from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
import sqlite3

print("🔥🔥🔥 AUTH.PY ЗАГРУЖЕН (ИСПРАВЛЕННАЯ ВЕРСИЯ) 🔥🔥🔥")

# ============================================
# НАСТРОЙКИ
# ============================================
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
# ============================================
# МИНИМАЛЬНЫЕ МОДЕЛИ
# ============================================
class Token(BaseModel):
    access_token: str
    token_type: str
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None
class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
# ============================================
# БАЗА ДАННЫХ
# ============================================
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn
def init_auth_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = pwd_context.hash("admin123")
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'admin@example.com', 'Administrator', 'admin'))
        print("✅ Создан тестовый admin/admin123")

    conn.commit()
    conn.close()
# ============================================
# ФУНКЦИИ
# ============================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def get_user(username: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password_hash, email, full_name, role FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "username": user[0],
            "password_hash": user[1],
            "email": user[2],
            "full_name": user[3],
            "role": user[4]
        }
    return None
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user
# ============================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================
init_auth_db()
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
# ============================================
# ЭНДПОИНТ ЛОГИНА
# ============================================
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"🔥 LOGIN: {form_data.username}")

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}
# ============================================
# ЭНДПОИНТ РЕГИСТРАЦИИ
# ============================================
@router.post("/register")
async def register(user: UserCreate):
    """
    Регистрация нового пользователя
    """
    print(f"🔥 REGISTER: {user.username}")
    print(f"📦 Данные: {user}")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username FROM users WHERE username = ? OR email = ?",
        (user.username, user.email)
    )
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    password_hash = get_password_hash(user.password)
    cursor.execute('''
        INSERT INTO users (username, password_hash, email, full_name, role)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.username, password_hash, user.email, user.full_name, 'user'))
    conn.commit()
    conn.close()
    print(f"✅ ПОЛЬЗОВАТЕЛЬ {user.username} СОЗДАН!")
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": 'user'
    }
# ============================================
# ЭНДПОИНТ /me
# ============================================
@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"]
    }