from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MedicaoBase(BaseModel):
    inversor_id: int
    timestamp: datetime
    potencia_ativa: float
    temperatura: Optional[float] = None

class MedicaoCreate(MedicaoBase):
    pass

class MedicaoUpdate(MedicaoBase):
    pass

class MedicaoRead(MedicaoBase):
    id: int
    class Config:
        orm_mode = True 