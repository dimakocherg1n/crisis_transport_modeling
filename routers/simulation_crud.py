from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
from typing import Optional
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

class SimulationCreate(BaseModel):
    id: Optional[int] = None
    name: str
    scenario_id: Optional[int] = None
    user_id: int
    status: str = "completed"
    created_at: str
    completed_at: Optional[str] = None
    results: str
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn
@router.post("/create")
async def create_simulation(
        simulation: SimulationCreate,
        current_user: dict = Depends(get_current_user)
):
    """Создание новой симуляции в БД"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        sim_id = simulation.id
        if not sim_id:
            cursor.execute("SELECT MAX(id) FROM simulations")
            max_id = cursor.fetchone()[0]
            sim_id = (max_id or 123) + 1
        cursor.execute('''
            INSERT INTO simulations 
            (id, name, scenario_id, user_id, status, created_at, completed_at, results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sim_id,
            simulation.name,
            simulation.scenario_id,
            simulation.user_id,
            simulation.status,
            simulation.created_at,
            simulation.completed_at or simulation.created_at,
            simulation.results
        ))
        conn.commit()
        return {
            "success": True,
            "simulation_id": sim_id,
            "message": "Симуляция успешно создана"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
@router.get("/list")
async def get_simulations(
        current_user: dict = Depends(get_current_user)
):
    """Получение списка симуляций пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, status, created_at, results
        FROM simulations
        WHERE user_id = (SELECT id FROM users WHERE username = ?)
        ORDER BY created_at DESC
        LIMIT 50
    ''', (current_user['username'],))
    simulations = cursor.fetchall()
    conn.close()
    return [dict(sim) for sim in simulations]