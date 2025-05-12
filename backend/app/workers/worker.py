import pika
import json
import os
from app.core.database import create_tables
from app.workers.process_ingestao import processa_ingestao
from app.workers.process_agregacao import (
    processa_potencia_maxima,
    processa_media_temperatura,
    processa_geracao_usina,
    processa_geracao_inversor
)

def processa_mensagem(ch, method, properties, body):
    try:
        mensagem = json.loads(body)
        tipo = mensagem.get('tipo')
        if tipo == 'ingestao':
            processa_ingestao(mensagem['dados'])
        elif tipo == 'potencia_maxima':
            processa_potencia_maxima(mensagem['parametros'])
        elif tipo == 'media_temperatura':
            processa_media_temperatura(mensagem['parametros'])
        elif tipo == 'geracao_usina':
            processa_geracao_usina(mensagem['parametros'])
        elif tipo == 'geracao_inversor':
            processa_geracao_inversor(mensagem['parametros'])
        else:
            print(f"Tipo de mensagem não suportado: {tipo}")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    create_tables()
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "processos")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=processa_mensagem)
    print(f"[Worker] Aguardando mensagens na fila '{RABBITMQ_QUEUE}'...")
    channel.start_consuming()

if __name__ == "__main__":
    main() 