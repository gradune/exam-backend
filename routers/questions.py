# routers/questions.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question
import openpyxl
from typing import List
from schemas import QuestionOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...), category: str = "General", db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    contents = await file.read()
    workbook = openpyxl.load_workbook(filename=bytes(contents), data_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(min_row=2, values_only=True))

    if not rows:
        raise HTTPException(status_code=400, detail="Excel file is empty or invalid format.")

    for row in rows:
        if len(row) < 6:
            continue  # skip incomplete rows

        question = Question(
            category=category,
            question=row[0],
            option_a=row[1],
            option_b=row[2],
            option_c=row[3],
            option_d=row[4],
            correct_option=row[5].upper()
        )
        db.add(question)

    db.commit()
    return {"message": f"{len(rows)} questions uploaded under category '{category}'."}

@router.get("/")
def get_questions(category: str, db: Session = Depends(get_db)) -> List[QuestionOut]:
    return db.query(Question).filter(Question.category == category).all()
