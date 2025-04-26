from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from models import User
import pandas as pd
from utils.excel_parser import parse_students_file, parse_questions_file
from typing import List
from models import Question, Response, Result, User
from schemas import SubmitResponses, StudentRegister, AdminCreate
import random
import re
from utils.auth import create_access_token, verify_token
from utils.dependencies import get_current_user
#from auth import hash_password  # assuming you hash passwords

models.Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or use ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register-user")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login_user(creds: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(creds.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.exam_completed and user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="You have already completed the exam.")
    access_token = create_access_token(data={"sub": user.email, "user_type": user.user_type, "id": user.id})
    return {"message": "Login successful", "user_type": user.user_type, "user_id": user.id,"name":user.name,"ID":user.user_id, "token":access_token, "user_stream": user.user_stream}

@app.post("/upload-questions/{category}")
def upload_questions(category: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    questions = parse_questions_file(file, category)
    for q in questions:
        db_question = models.Question(
            category=q['category'],
            question=q['question'],
            option_a=q['option_a'],
            option_b=q['option_b'],
            option_c=q['option_c'],
            option_d=q['option_d'],
            correct_option=q['correct_option']
        )
        db.add(db_question)
    db.commit()
    return {"message": f"Questions uploaded for {category}"}

@app.get("/questions/{category}")
def get_questions(category: str, db: Session = Depends(get_db)):
    #, loggedInUser=Depends(get_current_user)
    #print(loggedInUser)
    #print("loggedInUser")
    questions = db.query(models.Question).filter(models.Question.category == category.strip()).all()
    random.shuffle(questions)
    return questions[:250]
    #return db.query(models.Question).filter_by(category=category).all()

@app.post("/response")
def save_response(response: schemas.ResponseCreate, db: Session = Depends(get_db)):
    db.add(models.Response(**response.dict()))
    db.commit()
    return {"message": "Response saved"}

@app.get("/results/{student_id}")
def get_results(student_id: int, db: Session = Depends(get_db)):
    result = db.query(Result).filter(Result.student_id == student_id).first()
    responses = db.query(Response).filter(Response.student_id == student_id).all()
    return {
        "result": {
            "score": result.score,
            "total": result.total,
            "category": result.category
        } if result else None,
        "responses": [
            {"question_id": r.question_id, "selected_option": r.selected_option}
            for r in responses
        ]
    }

@app.post("/register-admin")
def register_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == admin.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists")

    hashed_password = pwd_context.hash(admin.password)
    user_id = generate_user_id(db, "ADMIN")
    new_admin = User(email=admin.email, password=hashed_password, user_type="admin", user_id=user_id)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"message": "Admin registered successfully", "id": new_admin.id}

@app.post("/register-single-student")
def register_student(student: StudentRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == student.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")


    db_stream = db.query(models.Stream).filter(models.Stream.name == student.user_stream).first()
    if not db_stream:
        new_stream = models.Stream(name=student.user_stream)
        db.add(new_stream)
        db.commit()
        db.refresh(new_stream)

    hashed_password = pwd_context.hash(student.password)
    stream = student.user_stream
    user_id = generate_user_id(db, stream)
    print(student)
    new_student = models.User(
        name=student.name,
        email=student.email,
        password=hashed_password,
        user_type='student',
        user_stream=student.user_stream,
        user_id=user_id,
        contact_number=student.contact_number,
        university=student.university,
        year_of_study=student.year_of_study
    )
    print(new_student)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"message": "Student registered successfully"}

@app.post("/upload-students")
def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    students_data = parse_students_file(file)
    for student in students_data:
        stream = student['stream']
        user_id = generate_user_id(db, stream)
        db_student = models.User(
            email=student['email'],
            password = pwd_context.hash(student['password']),
            user_type = 'student',
            user_stream = stream, # 
            name = student['name'],
            user_id = user_id,
            contact_number = student['contact_number'],
            university = student['university'],
            year_of_study = student['year_of_study']
        )
        db.add(db_student)
    db.commit()
    return {"message": "Students uploaded"}

@app.get("/students", response_model=List[dict])
def get_students(db: Session = Depends(get_db)):
    students = db.query(User).all()
    return [{"id": s.id, "email": s.email, "user_type": s.user_type, "exam_completed": s.exam_completed, "name":s.name,  "user_id":s.user_id, "stream":s.user_stream} for s in students]

@app.post("/submit-responses")
def submit_responses(payload: SubmitResponses, db: Session = Depends(get_db)):
    user_id = payload.user_id
    responses = payload.responses
    total_questions = payload.total_questions
    attempted  = len(responses)
    correct = 0

    student = db.query(User).filter(User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Delete existing responses and result if resubmitting
    db.query(Response).filter(Response.student_id == user_id).delete()
    db.query(Result).filter(Result.student_id == user_id).delete()
    db.commit()

    # Iterate through responses and compare
    for qid, selected in responses.items():
        question = db.query(Question).filter(Question.id == qid).first()
        if not question:
            continue

        if question.correct_option.strip().upper() == selected.strip().upper():
            correct += 1

        # Save the response
        db_response = Response(
            student_id=user_id,
            question_id=qid,
            selected_option=selected
        )
        db.add(db_response)

    db.commit()

    student.exam_completed = True
    db.commit()

    # Save result
    result = Result(
        student_id=user_id,
        category=student.user_stream,
        score=correct,
        total=total_questions,
        attempted=attempted 
    )
    db.add(result)
    db.commit()

    return {
        "message": "Responses submitted and result calculated",
        "total": total_questions,
        "attempted":attempted
    }

@app.post("/submit-responses-v2")
async def submit_responses_v2(request: SubmitResponses, db: Session = Depends(get_db)):
    body = await request.json()
    token = body.get("token")

    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/admin-results")
def get_all_student_results(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.user_type == "student").all()
    results = db.query(Result).all()

    result_map = {r.student_id: r for r in results}

    student_data = []
    for user in users:
        result = result_map.get(user.id)
        if result:
            status = "Completed"
            score = result.score
            total = result.total
        else:
            status = "Not Attempted"
            score = None
            total = None
        student_data.append({
            "id": user.id,
            "email": user.email,
            "stream": user.user_stream,
            "status": status,
            "score": score,
            "total": total
        })

    return student_data

@app.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}

@app.get("/questions/")
def get_paginated_questions(
    category: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    questions = db.query(models.Question)\
        .filter(models.Question.category == category.strip())\
        .offset(offset)\
        .limit(limit)\
        .all()

    total = db.query(models.Question).filter(models.Question.category == category.strip()).count()

    return {
        "questions": questions,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.delete("/user/{user_id}")
def delete_question(user_id: int, db: Session = Depends(get_db)):
    question = db.query(models.User).filter(models.User.id == user_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}

@app.put("/students/{student_id}/exam-status")
def update_exam_status(student_id: int, status: bool, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id).first()
    if student:
        student.exam_completed = status
        db.commit()
        return {"message": "Status updated"}
    raise HTTPException(status_code=404, detail="Student not found")

def clean_prefix(stream: str) -> str:
    # Extract only letters and uppercase the first 3 meaningful ones
    cleaned = re.sub(r'[^A-Za-z]', '', stream).upper()
    return cleaned[:3] if len(cleaned) >= 3 else cleaned.ljust(3, 'X')  # pad if <3

def generate_user_id(db: Session, stream: str) -> str:
    prefix = clean_prefix(stream)

    while True:
        user_id = f"{prefix}{random.randint(100, 999)}"
        exists = db.query(User).filter_by(user_id=user_id).first()
        if not exists:
            return user_id
        
@app.post("/streams/", response_model=schemas.StreamOut)
def create_stream(stream: schemas.StreamCreate, db: Session = Depends(get_db)):
    db_stream = db.query(models.Stream).filter(models.Stream.name == stream.name).first()
    if db_stream:
        raise HTTPException(status_code=400, detail="Stream already exists")
    new_stream = models.Stream(name=stream.name)
    db.add(new_stream)
    db.commit()
    db.refresh(new_stream)
    return new_stream

@app.get("/streams/", response_model=List[str])
def get_all_streams(db: Session = Depends(get_db), loggedInUser = Depends(get_current_user)):
    streams = db.query(models.Stream).all()
    return [s.name for s in streams]

@app.delete("/streams/{stream_id}")
def delete_stream(stream_id: int, db: Session = Depends(get_db)):
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    db.delete(stream)
    db.commit()
    return {"message": "Stream deleted successfully"}

@app.put("/streams/{stream_id}", response_model=schemas.StreamOut)
def update_stream(stream_id: int, updated: schemas.StreamUpdate, db: Session = Depends(get_db)):
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream.name = updated.name
    db.commit()
    db.refresh(stream)
    return stream