from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.inversor import InversorCreate, InversorRead, InversorUpdate
from app.crud import inversor as crud_inversor
from app.api.deps import get_db

router = APIRouter(prefix="/inversores", tags=["Inversores"])

@router.post("/", response_model=InversorRead, status_code=status.HTTP_201_CREATED)
def create_inversor(inversor: InversorCreate, db: Session = Depends(get_db)):
    return crud_inversor.create_inversor(db, inversor)

@router.get("/", response_model=List[InversorRead])
def list_inversores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_inversor.get_inversores(db, skip=skip, limit=limit)

@router.get("/{inversor_id}", response_model=InversorRead)
def get_inversor(inversor_id: int, db: Session = Depends(get_db)):
    db_inversor = crud_inversor.get_inversor(db, inversor_id)
    if not db_inversor:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    return db_inversor

@router.put("/{inversor_id}", response_model=InversorRead)
def update_inversor(inversor_id: int, inversor: InversorUpdate, db: Session = Depends(get_db)):
    db_inversor = crud_inversor.update_inversor(db, inversor_id, inversor)
    if not db_inversor:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    return db_inversor

@router.delete("/{inversor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inversor(inversor_id: int, db: Session = Depends(get_db)):
    success = crud_inversor.delete_inversor(db, inversor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    return None 