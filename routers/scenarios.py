from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

class ScenarioCreate(BaseModel):
    name: str
    description: str
    severity: int
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn
@router.post("/create")
async def create_scenario(
        scenario: ScenarioCreate,
        current_user: dict = Depends(get_current_user)
):
    print(f"\n📝 СОЗДАНИЕ СЦЕНАРИЯ:")
    print(f"   User: {current_user['username']}")
    print(f"   Name: {scenario.name}")
    print(f"   Severity: {scenario.severity}")
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (current_user['username'],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user[0]
        cursor.execute("SELECT MAX(id) FROM scenarios")
        max_id = cursor.fetchone()[0]
        scenario_id = (max_id or 0) + 1
        cursor.execute('''
            INSERT INTO scenarios (id, name, description, user_id, severity, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            scenario_id,
            scenario.name,
            scenario.description,
            user_id,
            scenario.severity,
            datetime.now().isoformat()
        ))
        conn.commit()
        print(f"✅ Сценарий {scenario_id} успешно создан!")
        return {
            "success": True,
            "scenario_id": scenario_id,
            "message": "Сценарий успешно создан"
        }
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
@router.get("/list")
async def list_scenarios(
        current_user: dict = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ?", (current_user['username'],))
        user = cursor.fetchone()
        if not user:
            return []
        user_id = user[0]
        cursor.execute('''
            SELECT id, name, description, severity, created_at
            FROM scenarios
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        scenarios = cursor.fetchall()
        result = []
        for s in scenarios:
            result.append({
                "id": s[0],
                "name": s[1],
                "description": s[2],
                "severity": s[3],
                "created_at": s[4]
            })
        return result
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []
    finally:
        conn.close()