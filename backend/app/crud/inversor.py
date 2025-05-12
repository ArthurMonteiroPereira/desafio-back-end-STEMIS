from sqlalchemy.orm import Session
from app.models.inversor import Inversor
from app.schemas.inversor import InversorCreate, InversorUpdate
from typing import List, Optional
from app.core.database import ajustar_sequencias

# Criar um inversor
def create_inversor(db: Session, inversor: InversorCreate) -> Inversor:
    data = inversor.dict()
    data.pop('id', None)  # Remove o campo id, se vier por engano
    db_inversor = Inversor(**data)
    db.add(db_inversor)
    db.commit()
    ajustar_sequencias()
    db.refresh(db_inversor)
    return db_inversor

# Listar todos os inversores
def get_inversores(db: Session, skip: int = 0, limit: int = 100) -> List[Inversor]:
    return db.query(Inversor).offset(skip).limit(limit).all()

# Buscar inversor por ID
def get_inversor(db: Session, inversor_id: int) -> Optional[Inversor]:
    return db.query(Inversor).filter(Inversor.id == inversor_id).first()

# Atualizar inversor
def update_inversor(db: Session, inversor_id: int, inversor: InversorUpdate) -> Optional[Inversor]:
    db_inversor = get_inversor(db, inversor_id)
    if not db_inversor:
        return None
    for key, value in inversor.dict(exclude_unset=True).items():
        setattr(db_inversor, key, value)
    db.commit()
    db.refresh(db_inversor)
    return db_inversor

# Deletar inversor
def delete_inversor(db: Session, inversor_id: int) -> bool:
    db_inversor = get_inversor(db, inversor_id)
    if not db_inversor:
        return False
    db.delete(db_inversor)
    db.commit()
    return True 