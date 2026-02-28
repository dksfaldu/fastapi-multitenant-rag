from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import bcrypt
from datetime import datetime
import os

from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

# SQLite setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Password hashing
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user") # 'admin' or 'user'
    
    projects = relationship("ProjectDB", back_populates="owner")

class ProjectDB(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    internal_id = Column(String, unique=True, index=True) # E.g. ui_admin_proj1
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="projects")

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Define default users
    default_users = [
        {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD, "role": "admin"},
    ]
    
    for u in default_users:
        user = db.query(User).filter(User.username == u["username"]).first()
        if not user:
            hashed = get_password_hash(u["password"])
            db_user = User(username=u["username"], password_hash=hashed, role=u["role"])
            db.add(db_user)
    
    db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
