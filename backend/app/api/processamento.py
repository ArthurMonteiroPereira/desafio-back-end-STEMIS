from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional, Dict, Any
import pika
import os
import json
from datetime import datetime, date
from app.api.deps import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/processamento", tags=["Processamento"])

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "processos")

@router.post("/iniciar", status_code=status.HTTP_202_ACCEPTED)
def iniciar_processamento(
    parametros: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Inicia um processamento de dados com os parâmetros especificados.
    
    Os parâmetros devem incluir:
    - tipo_processamento: string que identifica o tipo de processamento
    - filtros: objeto com filtros opcionais (datas, usinas, inversores)
    - configuracoes: configurações adicionais para o processamento
    """
    try:
        # Validar tipo de processamento
        tipo_processamento = parametros.get("tipo_processamento")
        if not tipo_processamento:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O tipo de processamento é obrigatório"
            )
        
        # Criar mensagem para a fila
        mensagem = json.dumps({
            "tipo": "processamento",
            "subtipo": tipo_processamento,
            "parametros": parametros,
            "data_solicitacao": datetime.now().isoformat()
        })
        
        # Enviar para a fila do RabbitMQ
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
        
        return {
            "msg": f"Processamento '{tipo_processamento}' iniciado com sucesso",
            "status": "em_processamento",
            "parametros": parametros
        }
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para processamento: {str(e)}")

@router.get("/status/{job_id}")
def verificar_status_processamento(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Verifica o status de um processamento específico pelo ID do job.
    """
    # Aqui seria implementada a consulta ao banco de dados para verificar o status
    # Por simplicidade, estamos retornando um status fixo
    return {
        "job_id": job_id,
        "status": "em_processamento",
        "iniciado_em": datetime.now().isoformat(),
        "progresso": 65
    }

@router.get("/tipos")
def listar_tipos_processamento():
    """
    Lista todos os tipos de processamento disponíveis no sistema.
    """
    tipos_processamento = [
        {
            "id": "analise_desempenho",
            "nome": "Análise de Desempenho",
            "descricao": "Avalia o desempenho dos inversores comparando com dados históricos"
        },
        {
            "id": "deteccao_anomalias",
            "nome": "Detecção de Anomalias",
            "descricao": "Identifica padrões anormais nas medições da usina"
        },
        {
            "id": "previsao_geracao",
            "nome": "Previsão de Geração",
            "descricao": "Projeta a geração futura com base em dados históricos e previsões meteorológicas"
        },
        {
            "id": "relatorio_eficiencia",
            "nome": "Relatório de Eficiência",
            "descricao": "Gera relatório detalhado sobre a eficiência da usina"
        }
    ]
    
    return tipos_processamento 