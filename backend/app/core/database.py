import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_tables():
    from app.models import Usina, Inversor, Medicao  # Garante que os modelos são importados
    Base.metadata.create_all(bind=engine)

def ajustar_sequencias():
    with engine.connect() as conn:
        conn.execute(text("SELECT setval('usinas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usinas));"))
        conn.execute(text("SELECT setval('inversores_id_seq', (SELECT COALESCE(MAX(id), 1) FROM inversores));"))
        conn.execute(text("SELECT setval('medicoes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM medicoes));"))
        conn.commit() 