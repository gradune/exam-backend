# In Python shell or migration script:
from models import Base
from database import engine
from passlib.context import CryptContext
from database import SessionLocal
from models import User


#Base.metadata.drop_all(bind=engine)
#Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()
hashed_pw = pwd_context.hash("admin123")

new_admin = User(email="admin@example.com", password=hashed_pw, user_type="admin")
db.add(new_admin)
db.commit()
db.close()

