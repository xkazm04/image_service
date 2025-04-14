from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from functions.generation import save_generation, get_all_generations, get_generation_by_id, get_generations_by_project_id
from schemas.generation import GenerationSchema
from database import get_db

router = APIRouter(tags=["Generations"])


@router.post("/")
def save_generation_endpoint(g: GenerationSchema, db: Session = Depends(get_db)):
    return save_generation(db, g.id, g.project_id, g.assigned_scene, g.prompt)


@router.get("/")
def get_all_generations_endpoint(db: Session = Depends(get_db)):
    generations = get_all_generations(db)
    return generations if generations else []


@router.get("/{generation_id}")
def get_generation_by_id_endpoint(generation_id: str, db: Session = Depends(get_db)):
    generation = get_generation_by_id(db, generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@router.get("/project/{project_id}")
def get_generations_by_project_id_endpoint(project_id: str, db: Session = Depends(get_db)):
    generations = get_generations_by_project_id(db, project_id)
    return generations if generations else []