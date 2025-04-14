from sqlalchemy.orm import Session
from models.models import Generation

# ----------- GENERATION CRUD FUNCTIONS ----------- #
def save_generation(db: Session, generation_id: str, project_id: str, assigned_scene: str = None):
    generation = Generation(id=generation_id, project_id=project_id, assigned_scene=assigned_scene)
    db.add(generation)
    db.commit()
    db.refresh(generation)
    return generation


def get_all_generations(db: Session):
    return db.query(Generation).all()


def get_generation_by_id(db: Session, generation_id: str):
    return db.query(Generation).filter(Generation.id == generation_id).first()


def get_generations_by_project_id(db: Session, project_id: str):
    return db.query(Generation).filter(Generation.project_id == project_id).all()