from sqlalchemy.orm import Session
from app.models.medicao import Medicao
from app.schemas.medicao import MedicaoCreate, MedicaoUpdate
from typing import List, Optional
from app.core.database import ajustar_sequencias

# Criar uma medição
def create_medicao(db: Session, medicao: MedicaoCreate) -> Medicao:
    data = medicao.dict()
    data.pop('id', None)  # Remove o campo id, se vier por engano
    db_medicao = Medicao(**data)
    db.add(db_medicao)
    db.commit()
    ajustar_sequencias()
    db.refresh(db_medicao)
    return db_medicao

# Listar medições (com filtros opcionais)
def get_medicoes(db: Session, skip: int = 0, limit: int = 100, inversor_id: Optional[int] = None) -> List[Medicao]:
    query = db.query(Medicao)
    if inversor_id:
        query = query.filter(Medicao.inversor_id == inversor_id)
    return query.offset(skip).limit(limit).all()

# Buscar medição por ID
def get_medicao(db: Session, medicao_id: int) -> Optional[Medicao]:
    return db.query(Medicao).filter(Medicao.id == medicao_id).first()

# Atualizar medição
def update_medicao(db: Session, medicao_id: int, medicao: MedicaoUpdate) -> Optional[Medicao]:
    db_medicao = get_medicao(db, medicao_id)
    if not db_medicao:
        return None
    for key, value in medicao.dict(exclude_unset=True).items():
        setattr(db_medicao, key, value)
    db.commit()
    db.refresh(db_medicao)
    return db_medicao

# Deletar medição
def delete_medicao(db: Session, medicao_id: int) -> bool:
    db_medicao = get_medicao(db, medicao_id)
    if not db_medicao:
        return False
    db.delete(db_medicao)
    db.commit()
    return True 