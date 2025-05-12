from fastapi import APIRouter, UploadFile, File, HTTPException, status
import pika
import os
import json

router = APIRouter(prefix="/ingestao", tags=["Ingestão"])

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "processos")

@router.post("/arquivo", status_code=status.HTTP_202_ACCEPTED)
def ingestao_arquivo(file: UploadFile = File(...)):
    try:
        conteudo = file.file.read()
        dados = json.loads(conteudo)
        mensagem = json.dumps({
            "tipo": "ingestao",
            "dados": dados
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
        return {"msg": "Arquivo enviado para processamento assíncrono."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}") 