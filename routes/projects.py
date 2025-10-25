from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from database import get_db
from services.image import create_project, get_project_by_id, list_projects
from models.models import Project
import logging

router = APIRouter(tags=["Projects"])
logger = logging.getLogger(__name__)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True

@router.post("/projects/", response_model=ProjectResponse)
def create_project_endpoint(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    try:
        return create_project(db, project.name, project.description)
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@router.get("/projects/", response_model=list[ProjectResponse])
def list_projects_endpoint(limit: int = 100, db: Session = Depends(get_db)):
    """List all projects"""
    try:
        projects = list_projects(db, limit)
        return projects
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    """Get a specific project"""
    try:
        project = get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")

@router.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    """Delete a project and all its images"""
    try:
        project = get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Mark all project images as deleted
        from models.models import Image
        db.query(Image).filter(Image.project_id == project_id).update({"status": "deleted"})
        
        # Delete the project
        db.delete(project)
        db.commit()
        
        return {"message": f"Project {project.name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete project")