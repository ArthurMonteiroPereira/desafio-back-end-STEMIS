from sqlalchemy.orm import Session
from app.models.usina import Usina
from app.schemas.usina import UsinaCreate, UsinaUpdate
from typing import List, Optional
from app.core.database import ajustar_sequencias

# Criar uma usina
def create_usina(db: Session, usina: UsinaCreate) -> Usina:
    data = usina.dict()
    data.pop('id', None)  # Remove o campo id, se vier por engano
    db_usina = Usina(**data)
    db.add(db_usina)
    db.commit()
    ajustar_sequencias()
    db.refresh(db_usina)
    return db_usina

# Listar todas as usinas
def get_usinas(db: Session, skip: int = 0, limit: int = 100) -> List[Usina]:
    return db.query(Usina).offset(skip).limit(limit).all()

# Buscar usina por ID
def get_usina(db: Session, usina_id: int) -> Optional[Usina]:
    return db.query(Usina).filter(Usina.id == usina_id).first()

# Atualizar usina
def update_usina(db: Session, usina_id: int, usina: UsinaUpdate) -> Optional[Usina]:
    db_usina = get_usina(db, usina_id)
    if not db_usina:
        return None
    for key, value in usina.dict(exclude_unset=True).items():
        setattr(db_usina, key, value)
    db.commit()
    db.refresh(db_usina)
    return db_usina

# Deletar usina
def delete_usina(db: Session, usina_id: int) -> bool:
    db_usina = get_usina(db, usina_id)
    if not db_usina:
        return False
    db.delete(db_usina)
    db.commit()
    return True 