# routers/exam.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Question, Result
from schemas import ExamSubmission
from typing import Dict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/submit")
def submit_exam(payload: ExamSubmission, db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.category == payload.category).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this category.")

    question_map: Dict[int, str] = {q.id: q.correct_option for q in questions}

    score = 0
    total = len(question_map)

    for qid, selected in payload.answers.items():
        correct = question_map.get(int(qid))
        if correct and selected.upper() == correct.upper():
            score += 1

    result = Result(
        email=payload.email,
        category=payload.category,
        score=score,
        total=total,
    )
    db.add(result)
    db.commit()

    return {
        "message": "Exam submitted",
        "score": score,
        "total": total
    }
