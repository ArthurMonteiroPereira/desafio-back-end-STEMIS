from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.usina import UsinaCreate, UsinaRead, UsinaUpdate
from app.crud import usina as crud_usina
from app.api.deps import get_db

router = APIRouter(prefix="/usinas", tags=["Usinas"])

@router.post("/", response_model=UsinaRead, status_code=status.HTTP_201_CREATED)
def create_usina(usina: UsinaCreate, db: Session = Depends(get_db)):
    return crud_usina.create_usina(db, usina)

@router.get("/", response_model=List[UsinaRead])
def list_usinas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_usina.get_usinas(db, skip=skip, limit=limit)

@router.get("/{usina_id}", response_model=UsinaRead)
def get_usina(usina_id: int, db: Session = Depends(get_db)):
    db_usina = crud_usina.get_usina(db, usina_id)
    if not db_usina:
        raise HTTPException(status_code=404, detail="Usina não encontrada")
    return db_usina

@router.put("/{usina_id}", response_model=UsinaRead)
def update_usina(usina_id: int, usina: UsinaUpdate, db: Session = Depends(get_db)):
    db_usina = crud_usina.update_usina(db, usina_id, usina)
    if not db_usina:
        raise HTTPException(status_code=404, detail="Usina não encontrada")
    return db_usina

@router.delete("/{usina_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usina(usina_id: int, db: Session = Depends(get_db)):
    success = crud_usina.delete_usina(db, usina_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usina não encontrada")
    return None 