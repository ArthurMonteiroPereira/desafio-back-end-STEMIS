from fastapi import FastAPI
from app.api import usina, inversor, medicao
from app.api import ingestao
from app.api import agregacao
from app.api import ia
from app.api import processamento

app = FastAPI()

app.include_router(usina.router)
app.include_router(inversor.router)
app.include_router(medicao.router)
app.include_router(ingestao.router)
app.include_router(agregacao.router)
app.include_router(ia.router)
app.include_router(processamento.router)

@app.get("/")
def read_root():
    return {"msg": "API de monitoramento de usinas fotovoltaicas"} 