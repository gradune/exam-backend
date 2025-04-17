# routers/results.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Result
from schemas import ResultOut
from typing import List
import openpyxl
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[ResultOut])
def get_results(email: str = Query(...), db: Session = Depends(get_db)):
    results = db.query(Result).filter(Result.email == email).all()
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this student.")
    return results

@router.get("/download")
def download_marksheet(email: str, db: Session = Depends(get_db)):
    results = db.query(Result).filter(Result.email == email).all()
    if not results:
        raise HTTPException(status_code=404, detail="No results found.")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Category", "Score", "Total", "Percentage"])

    for r in results:
        percentage = round((r.score / r.total) * 100, 2)
        ws.append([r.category, r.score, r.total, f"{percentage}%"])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"{email.replace('@', '_')}_marksheet.xlsx"
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

