from pydantic import BaseModel
from typing import Optional, List

class UsinaBase(BaseModel):
    nome: str
    localizacao: Optional[str] = None

class UsinaCreate(UsinaBase):
    pass

class UsinaUpdate(UsinaBase):
    pass

class UsinaRead(UsinaBase):
    id: int
    class Config:
        orm_mode = True 