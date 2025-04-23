from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import Dict

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    user_type = Column(String)  # 'admin' or 'student'
    user_stream = Column(String)  # 'commerce, bca, btech-it'
    exam_completed = Column(Boolean, default=False)
    contact_number = Column(String, nullable=True)
    university = Column(String, nullable=True)
    year_of_study = Column(String, nullable=True)
    name = Column(String)
    user_id = Column(String(10), unique=True, index=True, nullable=False)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    question = Column(String)
    option_a = Column(String)
    option_b = Column(String)
    option_c = Column(String)
    option_d = Column(String)
    correct_option = Column(String)

class Response(Base):
    __tablename__ = 'responses'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    selected_option = Column(String)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    category = Column(String)
    score = Column(Integer)
    total = Column(Integer)
    attempted = Column(Integer)

class Stream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
