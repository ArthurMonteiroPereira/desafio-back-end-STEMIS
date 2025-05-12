from app.core.database import SessionLocal
from sqlalchemy import func
from app.models import Medicao, Inversor
from datetime import datetime
from utils import calc_inverters_generation, TimeSeriesValue
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results_analises')
os.makedirs(RESULTS_DIR, exist_ok=True)

def salvar_resultado(tipo, parametros, resultado):
    nome = f"{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    caminho = os.path.join(RESULTS_DIR, nome)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump({"tipo": tipo, "parametros": parametros, "resultado": resultado}, f, ensure_ascii=False, indent=2)
    print(f"Arquivo de análise salvo em: {caminho}")

def processa_potencia_maxima(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        result = db.query(
            func.date(Medicao.timestamp).label('dia'),
            func.max(Medicao.potencia_ativa).label('potencia_maxima')
        ).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).group_by(func.date(Medicao.timestamp)).all()
        print(f"Potência máxima por dia: {result}")
        salvar_resultado('potencia_maxima', parametros, [dict(dia=str(r.dia), potencia_maxima=r.potencia_maxima) for r in result])
    finally:
        db.close()

def processa_media_temperatura(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        result = db.query(
            func.date(Medicao.timestamp).label('dia'),
            func.avg(Medicao.temperatura).label('media_temperatura')
        ).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).group_by(func.date(Medicao.timestamp)).all()
        print(f"Média de temperatura por dia: {result}")
        salvar_resultado('media_temperatura', parametros, [dict(dia=str(r.dia), media_temperatura=r.media_temperatura) for r in result])
    finally:
        db.close()

def processa_geracao_usina(parametros):
    db = SessionLocal()
    try:
        usina_id = parametros['usina_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        inversores = db.query(Inversor.id).filter(Inversor.usina_id == usina_id).all()
        inversor_ids = [inv.id for inv in inversores]
        entities_with_power = []
        for inversor_id in inversor_ids:
            medicoes = db.query(Medicao).filter(
                Medicao.inversor_id == inversor_id,
                Medicao.timestamp >= data_inicio,
                Medicao.timestamp <= data_fim
            ).order_by(Medicao.timestamp).all()
            power = [TimeSeriesValue(value=m.potencia_ativa, date=m.timestamp) for m in medicoes if m.potencia_ativa is not None]
            if power:
                entities_with_power.append(type('Entity', (), {'power': power})())
        geracao_total = calc_inverters_generation(entities_with_power)
        print(f"Geração total da usina (kWh): {geracao_total}")
        salvar_resultado('geracao_usina', parametros, geracao_total)
    finally:
        db.close()

def processa_geracao_inversor(parametros):
    db = SessionLocal()
    try:
        inversor_id = parametros['inversor_id']
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        medicoes = db.query(Medicao).filter(
            Medicao.inversor_id == inversor_id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).order_by(Medicao.timestamp).all()
        power = [TimeSeriesValue(value=m.potencia_ativa, date=m.timestamp) for m in medicoes if m.potencia_ativa is not None]
        entity = type('Entity', (), {'power': power})()
        geracao_total = calc_inverters_generation([entity])
        print(f"Geração total do inversor (kWh): {geracao_total}")
        salvar_resultado('geracao_inversor', parametros, geracao_total)
    finally:
        db.close() 