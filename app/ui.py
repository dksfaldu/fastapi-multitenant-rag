import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db, User, ProjectDB
from app.auth import (
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user_from_cookie,
    get_token_from_cookie
)
from jose import jwt, JWTError
from app.auth import SECRET_KEY, ALGORITHM

ui_router = APIRouter(tags=["ui"])

def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_cookie(request)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.username == username).first()

@ui_router.get("/", response_class=RedirectResponse)
async def root_redirect():
    """Redirects base path to the main application interface."""
    return RedirectResponse(url="/talktodoc")

@ui_router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, current_user: User = Depends(get_current_user_optional)):
    """Serves the standalone login page. Redirects if already authenticated."""
    if current_user:
        return RedirectResponse(url="/talktodoc", status_code=status.HTTP_303_SEE_OTHER)
        
    html_path = os.path.join(os.path.dirname(__file__), "login.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Login Template not found (login.html)</h1>"

@ui_router.get("/talktodoc", response_class=HTMLResponse)
async def get_talktodoc(request: Request, current_user: User = Depends(get_current_user_optional)):
    """Serves the main conversational and project management UI."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    html_path = os.path.join(os.path.dirname(__file__), "talktodoc.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        html = html.replace("{{USER_AUTH_STATE}}", "true")
        html = html.replace("{{USERNAME}}", current_user.username)
        html = html.replace("{{IS_ADMIN}}", "true" if current_user.role == "admin" else "false")
            
        return html
    except FileNotFoundError:
        return "<h1>UI Template not found (talktodoc.html)</h1>"

@ui_router.post("/auth/login")
async def login(
    response: Response,
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processes login and establishes session tokens via HttpOnly cookies."""
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    
    # We use a JSON response so the fetch() API grabs the cookie natively without redirect chaining
    from fastapi.responses import JSONResponse
    res = JSONResponse(content={"message": "ok"})
    res.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return res

@ui_router.post("/auth/logout")
async def logout(response: Response):
    """Purges active authentication parameters."""
    res = RedirectResponse(url="/talktodoc", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie(key="access_token")
    return res

@ui_router.get("/api/ui/projects")
async def get_user_projects(current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Fetches mapped projects accurately referencing DB architecture isolated to the querying user."""
    projects = db.query(ProjectDB).filter(ProjectDB.owner_id == current_user.id).all()
    out = []
    for p in projects:
        out.append({
            "id": p.id,
            "name": p.name,
            "internal_id": p.internal_id,
            "created_at": p.created_at.isoformat()
        })
    return out

@ui_router.post("/api/ui/projects")
async def create_user_project(
    name: str = Form(...),
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    """Spawn discrete RAG pipeline integration wrappers mapping an isolated target environment."""
    internal_id = f"ui_{current_user.id}_{uuid.uuid4().hex[:8]}"
    new_project = ProjectDB(name=name, internal_id=internal_id, owner_id=current_user.id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {
        "id": new_project.id,
        "name": new_project.name,
        "internal_id": new_project.internal_id
    }
