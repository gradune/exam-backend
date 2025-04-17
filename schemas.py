from pydantic import BaseModel
from typing import Dict
class AdminCreate(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    user_type: str
    user_stream: str
    exam_completed: bool
    name: str
    user_id: str

class LoginRequest(BaseModel):
    email: str
    password: str

class QuestionCreate(BaseModel):
    category: str
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str

class ResponseCreate(BaseModel):
    student_id: int
    question_id: int
    selected_option: str

class SubmitResponses(BaseModel):
    user_id: int
    responses: Dict[int, str]  # {question_id: selected_option}
    total_questions: int

class StreamBase(BaseModel):
    name: str

class StreamCreate(StreamBase):
    pass

class StreamUpdate(BaseModel):
    name: str
    
class StreamOut(StreamBase):
    id: int

    model_config = {
        "from_attributes": True
    }