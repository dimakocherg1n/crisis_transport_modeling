from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import sqlite3
import os
import uuid
import pandas as pd
import json
from datetime import datetime

from routers.auth import get_current_user

router = APIRouter(tags=["export"])
DB_PATH = r"C:\Users\kochergind\PycharmProjects\PythonProject3\crisis_transport_modeling\users.db"
EXPORT_DIR = r"C:\Users\kochergind\PycharmProjects\PythonProject3\crisis_transport_modeling\exports"
os.makedirs(EXPORT_DIR, exist_ok=True)
print(f"✅ Export router initialized (NO PREFIX!)")
print(f"📁 DB: {DB_PATH}")
print(f"📁 Export dir: {EXPORT_DIR}")
@router.get("/simulation/{simulation_id}/excel")
async def export_simulation_excel(
        simulation_id: int,
        current_user: dict = Depends(get_current_user)
):
    """Экспорт симуляции в Excel"""
    print(f"\n📊 ЗАПРОС ЭКСПОРТА EXCEL")
    print(f"   Simulation ID: {simulation_id}")
    print(f"   User: {current_user['username']}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, results 
            FROM simulations 
            WHERE id = ?
        """, (simulation_id,))
        sim = cursor.fetchone()
        conn.close()
        if not sim:
            print(f"❌ Симуляция {simulation_id} не найдена!")
            raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
        results = json.loads(sim[2]) if sim[2] else {}
        print(f"✅ Симуляция найдена: {sim[1]}")
        filename = f"simulation_{simulation_id}_{uuid.uuid4().hex[:8]}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)
        data = {
            'Parameter': ['Simulation ID', 'Name', 'Scenario', 'Vehicles', 'Deliveries', 'Efficiency'],
            'Value': [
                sim[0],
                sim[1],
                results.get('scenario', 'N/A'),
                results.get('vehicles', 'N/A'),
                results.get('deliveries', 'N/A'),
                f"{results.get('efficiency', 'N/A')}%"
            ]
        }
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
        return FileResponse(
            filepath,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=f"simulation_{simulation_id}_report.xlsx"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/simulation/{simulation_id}/csv")
async def export_simulation_csv(
        simulation_id: int,
):
    """Экспорт симуляции в CSV"""
    print(f"\n📈 ЗАПРОС ЭКСПОРТА CSV")
    print(f"   Simulation ID: {simulation_id}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, results 
            FROM simulations 
            WHERE id = ?
        """, (simulation_id,))
        sim = cursor.fetchone()
        conn.close()
        if not sim:
            raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
        results = json.loads(sim[2]) if sim[2] else {}
        filename = f"simulation_{simulation_id}_{uuid.uuid4().hex[:8]}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(f"Simulation ID,{sim[0]}\n")
            f.write(f"Name,{sim[1]}\n")
            f.write(f"Scenario,{results.get('scenario', 'N/A')}\n")
            f.write(f"Vehicles,{results.get('vehicles', 'N/A')}\n")
            f.write(f"Deliveries,{results.get('deliveries', 'N/A')}\n")
            f.write(f"Efficiency,{results.get('efficiency', 'N/A')}%\n")
        return FileResponse(
            filepath,
            media_type='text/csv',
            filename=f"simulation_{simulation_id}_data.csv"
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/simulation/{simulation_id}/pdf")
async def export_simulation_pdf(
        simulation_id: int,
):
    """Export simulation results to PDF (English only)"""
    print(f"\n📄 GENERATING PDF FOR SIMULATION {simulation_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, name, results 
            FROM simulations 
            WHERE id = ?
        """, (simulation_id,))
        sim = cursor.fetchone()
        if not sim:
            raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
        results = json.loads(sim[2]) if sim[2] else {}
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 20, f'Simulation Report #{simulation_id}', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'SIMULATION INFORMATION', 0, 1)
        pdf.ln(5)
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(50, 10, f'ID: {sim[0]}', 0, 1)
        pdf.cell(50, 10, f'Name: {sim[1]}', 0, 1)
        pdf.cell(50, 10, f'Scenario: {results.get("scenario", "N/A")}', 0, 1)
        pdf.cell(50, 10, f'Vehicles: {results.get("vehicles", "N/A")}', 0, 1)
        pdf.cell(50, 10, f'Deliveries: {results.get("deliveries", "N/A")}', 0, 1)
        pdf.cell(50, 10, f'Efficiency: {results.get("efficiency", "N/A")}%', 0, 1)
        pdf.ln(20)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 10, 'Generated by Crisis Transport Optimization API v2.0', 0, 1, 'C')
        filename = f"simulation_{simulation_id}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(EXPORT_DIR, filename)
        pdf.output(filepath)
        return FileResponse(
            filepath,
            media_type='application/pdf',
            filename=f"simulation_{simulation_id}_report.pdf"
        )
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
    finally:
        conn.close()