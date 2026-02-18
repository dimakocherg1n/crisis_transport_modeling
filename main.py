"""
Crisis Transport Optimization API v2.0
Главный модуль приложения
"""
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import sqlite3
from datetime import datetime
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Импортируем роутеры
from routers import auth
from routers.optimization import router as optimization_router
from routers.simulation import router as simulation_router
from routers.export import router as export_router
from routers.simulations import router as simulations_router
from routers.scenarios import router as scenarios_router

# Импортируем функцию get_current_user из auth
from routers.auth import get_current_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_TIME = time.time()

def init_database():
    """Инициализация базы данных и создание тестовых данных"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # ✅ УБИРАЕМ DROP TABLE - ТЕПЕРЬ ДАННЫЕ СОХРАНЯЮТСЯ!
    # cursor.execute("DROP TABLE IF EXISTS scenarios")

    # СОЗДАЕМ ТАБЛИЦУ СЦЕНАРИЕВ ТОЛЬКО ЕСЛИ ЕЁ НЕТ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            severity INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✅ Таблица scenarios проверена/создана")

    # Создаем таблицу simulations если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY,
            name TEXT,
            scenario_id INTEGER,
            user_id INTEGER,
            status TEXT,
            created_at TEXT,
            completed_at TEXT,
            results TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Создаем таблицу optimization_results если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS optimization_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulation_id INTEGER,
            algorithm TEXT,
            total_cost REAL,
            total_time REAL,
            vehicles_used INTEGER,
            routes TEXT,
            created_at TEXT,
            FOREIGN KEY (simulation_id) REFERENCES simulations (id)
        )
    ''')

    # Получаем admin пользователя
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()

    if admin:
        admin_id = admin[0]

        # Проверяем есть ли симуляция 123
        cursor.execute("SELECT id FROM simulations WHERE id = 123")
        if not cursor.fetchone():
            # Создаем тестовую симуляцию 123
            cursor.execute('''
                INSERT INTO simulations (id, name, user_id, status, created_at, completed_at, results)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                123,
                'Тестовая симуляция',
                admin_id,
                'completed',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps({
                    'deliveries': 78,
                    'avg_time': 2.3,
                    'efficiency': 85,
                    'vehicles': 15,
                    'duration': 12,
                    'intensity': 0.5,
                    'scenario': 'Тестовый сценарий'
                })
            ))
            print("✅ Создана тестовая симуляция 123")

        # ✅ ТОЛЬКО ЕСЛИ ТАБЛИЦА ПУСТАЯ - создаем тестовые сценарии
        cursor.execute("SELECT COUNT(*) FROM scenarios")
        count = cursor.fetchone()[0]

        if count == 0:
            test_scenarios = [
                (1, 'Землетрясение в регионе', 'Магнитуда 7.0, повреждены дороги', admin_id, 4, datetime.now().isoformat()),
                (2, 'Промышленная авария', 'Разлив химических веществ', admin_id, 3, datetime.now().isoformat()),
                (3, 'Забастовка водителей', 'Массовая забастовка', admin_id, 2, datetime.now().isoformat())
            ]

            for sc in test_scenarios:
                cursor.execute('''
                    INSERT OR IGNORE INTO scenarios (id, name, description, user_id, severity, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sc)
            print("✅ Созданы тестовые сценарии")
        else:
            print(f"📊 В таблице scenarios уже есть {count} записей, тестовые данные не добавлены")

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск Crisis Transport Optimization API...")
    print("=" * 60)
    init_database()
    yield
    print("👋 Завершение работы приложения...")

app = FastAPI(
    title="Crisis Transport Optimization API",
    description="API для оптимизации транспортных перевозок в кризисных ситуациях.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ПОДКЛЮЧАЕМ РОУТЕРЫ
# ============================================
print("✅ Подключение роутера аутентификации...")
app.include_router(auth.router)

print("✅ Подключение роутера оптимизации...")
app.include_router(optimization_router, prefix="/api/v1/optimization", tags=["optimization"])

print("✅ Подключение роутера симуляции...")
app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["simulation"])

print("✅ Подключение роутера экспорта...")
app.include_router(export_router, prefix="/api/v1/export", tags=["export"])

print("✅ Подключение роутера управления симуляциями...")
app.include_router(simulations_router)

print("✅ Подключение роутера сценариев...")
app.include_router(scenarios_router)

# ============================================
# БАЗОВЫЕ ЭНДПОИНТЫ
# ============================================
@app.get("/")
async def root():
    uptime = time.time() - START_TIME
    return {
        "name": "Crisis Transport Optimization API",
        "version": "2.0.0",
        "status": "operational",
        "uptime": f"{uptime:.2f} seconds",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/api/v1/auth",
            "optimization": "/api/v1/optimization",
            "simulation": "/api/v1/simulation",
            "export": "/api/v1/export",
            "simulations": "/api/v1/simulations",
            "scenarios": "/api/v1/scenarios"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "database": "connected"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

print("=" * 60)
print("✅ CRISIS TRANSPORT OPTIMIZATION API v2.0 УСПЕШНО ЗАПУЩЕНО!")
print(f"📚 Документация: http://localhost:8001/docs")
print(f"❤️ Health check: http://localhost:8001/health")
print(f"🔐 Аутентификация: http://localhost:8001/api/v1/auth")
print(f"🚛 Оптимизация: http://localhost:8001/api/v1/optimization")
print(f"📊 Симуляция: http://localhost:8001/api/v1/simulation")
print(f"📄 Экспорт: http://localhost:8001/api/v1/export")
print(f"🆕 Создание симуляций: http://localhost:8001/api/v1/simulations/create")
print(f"📋 Список симуляций: http://localhost:8001/api/v1/simulations/list")
print(f"🎭 Создание сценариев: http://localhost:8001/api/v1/scenarios/create")
print(f"📚 Список сценариев: http://localhost:8001/api/v1/scenarios/list")
print("=" * 60)