from pydantic import BaseModel
from typing import Optional

class InversorBase(BaseModel):
    nome: str
    modelo: Optional[str] = None
    usina_id: int

class InversorCreate(InversorBase):
    pass

class InversorUpdate(InversorBase):
    pass

class InversorRead(InversorBase):
    id: int
    class Config:
        orm_mode = True 