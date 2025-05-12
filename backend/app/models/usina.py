from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Usina(Base):
    __tablename__ = "usinas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    localizacao = Column(String, nullable=True)

    inversores = relationship("Inversor", back_populates="usina", cascade="all, delete-orphan") 