from sqlalchemy.orm import Session
from app import models

def create_load(db: Session, load_data):
    db_load = models.Load(**load_data)
    db.add(db_load)
    db.commit()
    db.refresh(db_load)
    return db_load

def get_loads(db: Session):
    return db.query(models.Load).all()

def get_load_by_id(db: Session, load_id: str):
    return db.query(models.Load).filter(models.Load.load_id == load_id).first()
