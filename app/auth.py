from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db, User, verify_password, get_password_hash
from app.config import ADMIN_USERNAME

SECRET_KEY = "super-secret-rag-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# We use this primarily to get the token from cookies for UI endpoints
def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    return token

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user_from_cookie)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
