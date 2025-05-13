from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pika
import os
import json
from datetime import datetime

router = APIRouter(prefix="/ia", tags=["Inteligência Artificial"])

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "processos")

class TreinarModelosParams(BaseModel):
    data_inicio: str
    data_fim: str

@router.post("/treinar", status_code=status.HTTP_202_ACCEPTED)
def treinar_modelos(params: TreinarModelosParams):
    """
    Solicita o treinamento de modelos de inteligência artificial com base nos dados do período especificado.
    O treinamento é executado de forma assíncrona.
    """
    try:
        mensagem = json.dumps({
            "tipo": "treinar_modelos",
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
        return {"msg": "Solicitação de treinamento de modelos enviada para processamento assíncrono. Este processo pode demorar alguns minutos."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar para fila: {str(e)}")

@router.get("/status", status_code=status.HTTP_200_OK)
def obter_status_modelos():
    """
    Obtém o status dos modelos treinados, incluindo a data do último treinamento
    e métricas de desempenho.
    """
    try:
        from app.workers.process_ia import obter_status_modelos
        resultado = obter_status_modelos()
        if resultado:
            return resultado
        # Se não há modelos treinados, retornar um status em vez de lançar exceção
        return {
            "status": "nao_treinado",
            "mensagem": "Nenhum modelo treinado encontrado. Use o endpoint /ia/treinar para iniciar o treinamento."
        }
    except ImportError as e:
        # Erro específico para módulo não encontrado
        return {
            "status": "erro",
            "mensagem": "Módulo de IA não está configurado corretamente",
            "detalhes": str(e)
        }
    except Exception as e:
        # Para outros erros, registrar e retornar informações úteis
        import traceback
        print(f"Erro ao obter status dos modelos: {str(e)}")
        print(traceback.format_exc())
        
        return {
            "status": "erro",
            "mensagem": "Erro ao verificar status dos modelos",
            "detalhes": str(e)
        }

@router.get("/insights", status_code=status.HTTP_200_OK)
def obter_insights(data_inicio: str, data_fim: str):
    """
    Gera insights com base nos modelos treinados para o período especificado.
    """
    try:
        from app.workers.process_ia import gerar_insights
        resultado = gerar_insights(data_inicio, data_fim)
        if resultado:
            return resultado
        raise HTTPException(status_code=404, detail="Não foi possível gerar insights para o período especificado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights: {str(e)}")

@router.get("/previsao/geracao", status_code=status.HTTP_200_OK)
def prever_geracao(usina_id: int, dias: int = 7):
    """
    Realiza previsão de geração para uma usina específica para os próximos X dias.
    """
    try:
        from app.workers.process_ia import prever_geracao
        resultado = prever_geracao(usina_id, dias)
        if resultado:
            return resultado
        raise HTTPException(status_code=404, detail=f"Não foi possível gerar previsão para a usina {usina_id}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar previsão: {str(e)}")

@router.get("/anomalias", status_code=status.HTTP_200_OK)
def detectar_anomalias(data_inicio: str, data_fim: str):
    """
    Detecta anomalias no funcionamento das usinas e inversores no período especificado.
    """
    try:
        print(f"Iniciando detecção de anomalias para o período: {data_inicio} a {data_fim}")
        from app.workers.process_ia import detectar_anomalias
        
        # Verificar se o modelo existe antes de chamá-lo
        import os
        from app.workers.process_ia import MODELO_ANOMALIAS
        if not os.path.exists(MODELO_ANOMALIAS):
            print(f"Modelo de anomalias não encontrado em: {MODELO_ANOMALIAS}")
            return {
                "status": "nao_treinado",
                "mensagem": "Modelo de detecção de anomalias não treinado. Use o endpoint /ia/treinar primeiro."
            }
            
        # Chamar a função de detecção com tratamento de erros
        try:
            resultado = detectar_anomalias(data_inicio, data_fim)
            if resultado:
                print(f"Detecção de anomalias concluída com sucesso. {resultado.get('total_anomalias', 0)} anomalias encontradas.")
                return resultado
            
            print("A função de detecção não retornou resultados")
            return {
                "anomalias": [],
                "total_anomalias": 0,
                "mensagem": "Nenhuma anomalia detectada no período especificado"
            }
        except Exception as e:
            import traceback
            print(f"Erro na função de detecção de anomalias: {str(e)}")
            print(traceback.format_exc())
            raise
            
    except Exception as e:
        import traceback
        print(f"Erro ao detectar anomalias: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao detectar anomalias: {str(e)}") 