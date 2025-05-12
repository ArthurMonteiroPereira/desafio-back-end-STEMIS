from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Inversor(Base):
    __tablename__ = "inversores"

    id = Column(Integer, primary_key=True, index=True)
    usina_id = Column(Integer, ForeignKey("usinas.id"), nullable=False)
    nome = Column(String, nullable=False)
    modelo = Column(String, nullable=True)

    usina = relationship("Usina", back_populates="inversores")
    medicoes = relationship("Medicao", back_populates="inversor", cascade="all, delete-orphan") 