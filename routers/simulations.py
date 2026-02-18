"""
Роутер для управления симуляциями
Создание, чтение, список симуляций
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json
from typing import Optional, Dict, Any, List

from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])
class SimulationCreate(BaseModel):
    name: str
    vehicles: int
    duration: int
    intensity: float
    scenario: str
class SimulationResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: str
    results: Dict[str, Any]
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
    print(f"\n📝 СОЗДАНИЕ СИМУЛЯЦИИ:")
    print(f"   User: {current_user['username']}")
    print(f"   Scenario: {simulation.scenario}")
    print(f"   Vehicles: {simulation.vehicles}")
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (current_user['username'],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user[0]
        cursor.execute("SELECT MAX(id) FROM simulations")
        max_id = cursor.fetchone()[0]
        sim_id = (max_id or 123) + 1
        print(f"   Generated ID: {sim_id}")
        deliveries = int(simulation.vehicles * (1 + (1 - simulation.intensity) * 0.5))
        avg_time = round(1.5 + simulation.intensity * 1.5, 1)
        efficiency = int((1 - simulation.intensity * 0.4) * 90)
        total_cost = int(deliveries * 300 + simulation.vehicles * 500)
        results = {
            "scenario": simulation.scenario,
            "vehicles": simulation.vehicles,
            "duration": simulation.duration,
            "intensity": simulation.intensity,
            "deliveries": deliveries,
            "avg_time": avg_time,
            "efficiency": efficiency,
            "total_cost": total_cost,
            "timestamp": datetime.now().isoformat()
        }
        cursor.execute('''
            INSERT INTO simulations 
            (id, name, user_id, status, created_at, completed_at, results)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            sim_id,
            f"Симуляция: {simulation.scenario[:30]}",
            user_id,
            'completed',
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(results, ensure_ascii=False)
        ))
        cursor.execute('''
            INSERT INTO optimization_results 
            (simulation_id, algorithm, total_cost, total_time, vehicles_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            sim_id,
            'genetic',
            results['total_cost'],
            simulation.duration * (0.8 + simulation.intensity * 0.4),
            simulation.vehicles,
            datetime.now().isoformat()
        ))
        conn.commit()
        print(f"✅ Симуляция {sim_id} успешно создана!")
        return {
            "success": True,
            "simulation_id": sim_id,
            "results": results
        }
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
@router.get("/list")
async def list_simulations(
        current_user: dict = Depends(get_current_user),
        limit: int = 50
):
    """Список симуляций пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (current_user['username'],))
        user = cursor.fetchone()
        if not user:
            return []
        user_id = user[0]
        cursor.execute('''
            SELECT id, name, status, created_at, results
            FROM simulations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        simulations = cursor.fetchall()
        result = []
        for sim in simulations:
            result.append({
                "id": sim[0],
                "name": sim[1],
                "status": sim[2],
                "created_at": sim[3],
                "results": json.loads(sim[4]) if sim[4] else {}
            })
        return result
    finally:
        conn.close()

@router.get("/{simulation_id}")
async def get_simulation(
        simulation_id: int,
        current_user: dict = Depends(get_current_user)
):
    """Получение конкретной симуляции"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (current_user['username'],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]
    cursor.execute('''
        SELECT id, name, status, created_at, results
        FROM simulations
        WHERE id = ? AND user_id = ?
    ''', (simulation_id, user_id))
    sim = cursor.fetchone()
    conn.close()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {
        "id": sim[0],
        "name": sim[1],
        "status": sim[2],
        "created_at": sim[3],
        "results": json.loads(sim[4]) if sim[4] else {}
    }