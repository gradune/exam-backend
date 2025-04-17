from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set in environment")
#DATABASE_URL = "postgresql://postgres:''@localhost/postgres"
#host=localhost port=5432 dbname=postgres user=postgres connect_timeout=10 sslmode=prefer

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False,bind=engine, autoflush=False)
Base = declarative_base() 
