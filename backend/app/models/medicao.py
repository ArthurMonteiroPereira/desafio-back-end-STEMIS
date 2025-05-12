from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Medicao(Base):
    __tablename__ = "medicoes"

    id = Column(Integer, primary_key=True, index=True)
    inversor_id = Column(Integer, ForeignKey("inversores.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    potencia_ativa = Column(Float, nullable=True)
    temperatura = Column(Float, nullable=True)

    inversor = relationship("Inversor", back_populates="medicoes") 