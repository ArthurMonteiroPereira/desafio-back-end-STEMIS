from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
import pika
import os
import json

router = APIRouter(prefix="/agregacao", tags=["Agregação"])

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "processos")

class PotenciaMaximaParams(BaseModel):
    inversor_id: int
    data_inicio: str
    data_fim: str

@router.post("/potencia_maxima", status_code=status.HTTP_202_ACCEPTED)
def potencia_maxima(params: PotenciaMaximaParams):
    try:
        mensagem = json.dumps({
            "tipo": "potencia_maxima",
            "parametros": params.dict()
        })
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=mensagem.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return {"msg": "Solicitação de potência máxima enviada para processamento assíncrono."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}")

class MediaTemperaturaParams(BaseModel):
    inversor_id: int
    data_inicio: str
    data_fim: str

@router.post("/media_temperatura", status_code=status.HTTP_202_ACCEPTED)
def media_temperatura(params: MediaTemperaturaParams):
    try:
        mensagem = json.dumps({
            "tipo": "media_temperatura",
            "parametros": params.dict()
        })
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=mensagem.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return {"msg": "Solicitação de média de temperatura enviada para processamento assíncrono."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}")

class GeracaoUsinaParams(BaseModel):
    usina_id: int
    data_inicio: str
    data_fim: str

@router.post("/geracao_usina", status_code=status.HTTP_202_ACCEPTED)
def geracao_usina(params: GeracaoUsinaParams):
    try:
        mensagem = json.dumps({
            "tipo": "geracao_usina",
            "parametros": params.dict()
        })
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=mensagem.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return {"msg": "Solicitação de geração da usina enviada para processamento assíncrono."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}")

class GeracaoInversorParams(BaseModel):
    inversor_id: int
    data_inicio: str
    data_fim: str

@router.post("/geracao_inversor", status_code=status.HTTP_202_ACCEPTED)
def geracao_inversor(params: GeracaoInversorParams):
    try:
        mensagem = json.dumps({
            "tipo": "geracao_inversor",
            "parametros": params.dict()
        })
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=mensagem.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return {"msg": "Solicitação de geração do inversor enviada para processamento assíncrono."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}") 