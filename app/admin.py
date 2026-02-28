import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD
from app.logger import get_all_projects_stats, get_project_logs
from app.database import get_db, User, ProjectDB, get_password_hash

class UserCreate(BaseModel):
    username: str
    password: str

admin_router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@admin_router.get("", response_class=HTMLResponse)
async def admin_dashboard_view(admin: str = Depends(get_current_admin)):
    """Serves the main Admin UI HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "admin_dashboard.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Dashboard HTML not found</h1>"

@admin_router.get("/api/stats")
async def get_stats(admin: str = Depends(get_current_admin), db: Session = Depends(get_db)):
    """API endpoint backing the dashboard: returns tracking info about active projects."""
    stats = get_all_projects_stats()
    # Enrich stats with the project creator's username
    enriched_stats = []
    for stat in stats:
        proj = db.query(ProjectDB).filter(ProjectDB.internal_id == stat["project_id"]).first()
        owner_username = "Unknown"
        if proj and proj.owner:
            owner_username = proj.owner.username
            
        stat["creator"] = owner_username
        enriched_stats.append(stat)
        
    return enriched_stats

@admin_router.post("/api/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    admin: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Endpoint for admins to create new users."""
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, password_hash=hashed_pwd, role="user")
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": f"User '{new_user.username}' created successfully."}

@admin_router.get("/api/logs/{project_id}")
async def get_logs(project_id: str, admin: str = Depends(get_current_admin)):
    """API endpoint returning specific API interaction logs matching the tenant requested."""
    return {"project_id": project_id, "logs": get_project_logs(project_id)}
