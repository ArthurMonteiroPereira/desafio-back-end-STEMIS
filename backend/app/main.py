from fastapi import FastAPI
from app.api import usina, inversor, medicao
from app.api import ingestao
from app.api import agregacao

app = FastAPI()

app.include_router(usina.router)
app.include_router(inversor.router)
app.include_router(medicao.router)
app.include_router(ingestao.router)
app.include_router(agregacao.router)

@app.get("/")
def read_root():
    return {"msg": "API de monitoramento de usinas fotovoltaicas"} 