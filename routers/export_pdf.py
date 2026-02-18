"""
PDF Export Module - Standalone version
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from openpyxl import Workbook
import os
import uuid
import csv


router = APIRouter(tags=["export"])  # Убрали prefix!

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


@router.get("/simulation/{simulation_id}/pdf")
async def export_simulation_pdf(
        simulation_id: int
):
    """Simple PDF test - no auth, no DB, just a test"""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 20, f'Test PDF Report #{simulation_id}', 0, 1, 'C')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 10, f'Created: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1, 'R')
        filename = f"test_{simulation_id}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(EXPORT_DIR, filename)
        pdf.output(filepath)
        return FileResponse(
            filepath,
            media_type='application/pdf',
            filename=f"test_report_{simulation_id}.pdf"
        )
    except Exception as e:
        print(f"PDF Error: {e}")

        raise HTTPException(status_code=500, detail=str(e))
