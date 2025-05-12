from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.medicao import MedicaoCreate, MedicaoRead, MedicaoUpdate
from app.crud import medicao as crud_medicao
from app.api.deps import get_db

router = APIRouter(prefix="/medicoes", tags=["Medicoes"])

@router.post("/", response_model=MedicaoRead, status_code=status.HTTP_201_CREATED)
def create_medicao(medicao: MedicaoCreate, db: Session = Depends(get_db)):
    return crud_medicao.create_medicao(db, medicao)

@router.get("/", response_model=List[MedicaoRead])
def list_medicoes(skip: int = 0, limit: int = 100, inversor_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud_medicao.get_medicoes(db, skip=skip, limit=limit, inversor_id=inversor_id)

@router.get("/{medicao_id}", response_model=MedicaoRead)
def get_medicao(medicao_id: int, db: Session = Depends(get_db)):
    db_medicao = crud_medicao.get_medicao(db, medicao_id)
    if not db_medicao:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    return db_medicao

@router.put("/{medicao_id}", response_model=MedicaoRead)
def update_medicao(medicao_id: int, medicao: MedicaoUpdate, db: Session = Depends(get_db)):
    db_medicao = crud_medicao.update_medicao(db, medicao_id, medicao)
    if not db_medicao:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    return db_medicao

@router.delete("/{medicao_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicao(medicao_id: int, db: Session = Depends(get_db)):
    success = crud_medicao.delete_medicao(db, medicao_id)
    if not success:
        raise HTTPException(status_code=404, detail="Medição não encontrada")
    return None 