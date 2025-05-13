import json
import os
import time
from datetime import datetime, timedelta
import random
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import medicao, inversor, usina

def log_processamento(mensagem):
    """
    Registra log do processamento com timestamp
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [PROCESSAMENTO] {mensagem}")

def salvar_resultado(tipo_processamento, resultado, parametros=None):
    """
    Salva o resultado do processamento em arquivo para posterior consulta
    """
    # Criar diretório para resultados caso não exista
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, 'results_processamento')
    os.makedirs(results_dir, exist_ok=True)
    
    # Criar nome de arquivo único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{tipo_processamento}_{timestamp}.json"
    file_path = os.path.join(results_dir, filename)
    
    # Salvar resultado em arquivo JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({
            "tipo": tipo_processamento,
            "data_execucao": datetime.now().isoformat(),
            "parametros": parametros or {},
            "resultado": resultado
        }, f, indent=2, ensure_ascii=False)
    
    log_processamento(f"Resultado salvo em: {file_path}")
    return file_path

def processar_analise_desempenho(parametros):
    """
    Executa análise de desempenho dos inversores com base em dados históricos
    """
    log_processamento("Iniciando análise de desempenho")
    
    # Simulando processamento intensivo
    time.sleep(2)
    
    # Criar sessão do banco de dados
    db = SessionLocal()
    try:
        # Simulação de análise completa
        # Em produção, aqui seria feita a consulta real ao banco de dados
        
        # Obter inversores para análise
        inversores_ids = parametros.get("inversores_ids", [])
        usina_id = parametros.get("usina_id")
        
        # Se não houver inversores especificados mas houver usina, buscar todos os inversores da usina
        if not inversores_ids and usina_id:
            # Simulando busca de inversores da usina
            inversores_ids = [1, 2, 3, 4]  # IDs fictícios
        
        # Resultados simulados da análise
        resultados = []
        for inv_id in inversores_ids:
            eficiencia = random.uniform(0.75, 0.98)
            desempenho_relativo = random.uniform(0.9, 1.1)
            
            resultados.append({
                "inversor_id": inv_id,
                "eficiencia": round(eficiencia, 4),
                "desempenho_relativo": round(desempenho_relativo, 4),
                "status": "normal" if desempenho_relativo > 0.95 else "atenção",
                "anomalias_detectadas": desempenho_relativo < 0.95
            })
        
        # Estatísticas gerais
        estatisticas = {
            "eficiencia_media": round(sum(r["eficiencia"] for r in resultados) / len(resultados), 4),
            "desempenho_medio": round(sum(r["desempenho_relativo"] for r in resultados) / len(resultados), 4),
            "inversores_analisados": len(resultados),
            "inversores_com_anomalias": sum(1 for r in resultados if r["anomalias_detectadas"])
        }
        
        resultado_final = {
            "estatisticas": estatisticas,
            "detalhamento": resultados,
            "periodo_analisado": {
                "inicio": (datetime.now() - timedelta(days=30)).isoformat(),
                "fim": datetime.now().isoformat()
            }
        }
        
        # Salvar resultado
        arquivo_resultado = salvar_resultado("analise_desempenho", resultado_final, parametros)
        log_processamento(f"Análise de desempenho concluída com sucesso")
        
        return arquivo_resultado
    
    finally:
        db.close()

def processar_deteccao_anomalias(parametros):
    """
    Executa detecção de anomalias nas medições
    """
    log_processamento("Iniciando detecção de anomalias")
    
    # Simulando processamento intensivo
    time.sleep(3)
    
    # Criar sessão do banco de dados
    db = SessionLocal()
    try:
        # Simulação de detecção de anomalias
        
        # Dados simulados de anomalias detectadas
        anomalias = []
        for _ in range(random.randint(3, 8)):
            tipo_anomalia = random.choice([
                "queda_brusca_potencia", 
                "oscilacao_excessiva", 
                "temperatura_elevada",
                "baixo_rendimento_constante"
            ])
            
            data_deteccao = datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            anomalias.append({
                "tipo": tipo_anomalia,
                "severidade": random.choice(["baixa", "média", "alta"]),
                "data_deteccao": data_deteccao.isoformat(),
                "inversor_id": random.randint(1, 5),
                "confiabilidade": round(random.uniform(0.7, 0.99), 2),
                "descricao": f"Anomalia do tipo {tipo_anomalia} detectada"
            })
        
        # Ordenar anomalias por severidade
        severidade_ordem = {"alta": 0, "média": 1, "baixa": 2}
        anomalias.sort(key=lambda x: severidade_ordem[x["severidade"]])
        
        resultado_final = {
            "total_anomalias": len(anomalias),
            "anomalias": anomalias,
            "recomendacoes": [
                "Verificar conexões dos inversores com anomalias severas",
                "Agendar manutenção preventiva para inversores com temperatura elevada",
                "Verificar sombreamento em painéis com baixo rendimento constante"
            ]
        }
        
        # Salvar resultado
        arquivo_resultado = salvar_resultado("deteccao_anomalias", resultado_final, parametros)
        log_processamento(f"Detecção de anomalias concluída com sucesso")
        
        return arquivo_resultado
    
    finally:
        db.close()

def processar_previsao_geracao(parametros):
    """
    Executa previsão de geração futura baseada em dados históricos
    """
    log_processamento("Iniciando previsão de geração")
    
    # Simulando processamento intensivo
    time.sleep(2.5)
    
    # Parâmetros de previsão
    dias_previsao = parametros.get("dias_previsao", 7)
    usina_id = parametros.get("usina_id")
    
    # Criar sessão do banco de dados
    db = SessionLocal()
    try:
        # Simulação de previsão de geração
        
        # Dados históricos de geração simulados (7 dias anteriores)
        historico = []
        data_base = datetime.now() - timedelta(days=7)
        
        for dia in range(7):
            data_atual = data_base + timedelta(days=dia)
            
            # Simulando variação diária com alguma aleatoriedade
            geracao_base = random.uniform(800, 1200)  # kWh base
            # Mais geração nos dias de meio da semana (simulando padrão)
            fator_dia = 1.0 + 0.1 * (3 - abs(dia - 3)) / 3
            
            geracao = geracao_base * fator_dia
            
            historico.append({
                "data": data_atual.strftime("%Y-%m-%d"),
                "geracao_kwh": round(geracao, 2),
                "radiacao_media": round(random.uniform(4.5, 6.2), 1),
                "temperatura_media": round(random.uniform(22, 28), 1)
            })
        
        # Previsão simulada para os próximos dias
        previsao = []
        data_inicio_previsao = datetime.now()
        
        for dia in range(dias_previsao):
            data_atual = data_inicio_previsao + timedelta(days=dia)
            
            # Base na média histórica com alguma variação
            media_historica = sum(h["geracao_kwh"] for h in historico) / len(historico)
            
            # Fator de variação baseado no dia da semana
            dia_semana = data_atual.weekday()
            fator_dia = 1.0 + 0.1 * (3 - abs(dia_semana - 3)) / 3
            
            # Adicionar alguma tendência e ruído
            tendencia = 1.0 + dia * 0.01  # Pequena tendência de aumento
            ruido = random.uniform(0.9, 1.1)
            
            geracao_prevista = media_historica * fator_dia * tendencia * ruido
            
            previsao.append({
                "data": data_atual.strftime("%Y-%m-%d"),
                "geracao_prevista_kwh": round(geracao_prevista, 2),
                "intervalo_confianca": {
                    "minimo": round(geracao_prevista * 0.85, 2),
                    "maximo": round(geracao_prevista * 1.15, 2)
                },
                "confiabilidade": round(random.uniform(0.7, 0.9), 2)
            })
        
        resultado_final = {
            "usina_id": usina_id,
            "data_previsao": datetime.now().isoformat(),
            "dias_previstos": dias_previsao,
            "geracao_total_prevista": round(sum(p["geracao_prevista_kwh"] for p in previsao), 2),
            "historico": historico,
            "previsao_diaria": previsao
        }
        
        # Salvar resultado
        arquivo_resultado = salvar_resultado("previsao_geracao", resultado_final, parametros)
        log_processamento(f"Previsão de geração concluída com sucesso")
        
        return arquivo_resultado
    
    finally:
        db.close()

def processar_relatorio_eficiencia(parametros):
    """
    Gera relatório detalhado de eficiência da usina
    """
    log_processamento("Iniciando geração de relatório de eficiência")
    
    # Simulando processamento intensivo
    time.sleep(4)
    
    # Parâmetros
    periodo_inicio = parametros.get("periodo_inicio")
    periodo_fim = parametros.get("periodo_fim", datetime.now().isoformat())
    usina_id = parametros.get("usina_id")
    
    # Criar sessão do banco de dados
    db = SessionLocal()
    try:
        # Simulação de geração de relatório
        
        # Dados de eficiência simulados
        metricas_gerais = {
            "eficiencia_media": round(random.uniform(0.82, 0.94), 4),
            "performance_ratio": round(random.uniform(0.75, 0.88), 4),
            "disponibilidade": round(random.uniform(0.95, 0.995), 4),
            "perda_por_temperatura": f"{round(random.uniform(2, 8), 1)}%",
            "perda_por_sombreamento": f"{round(random.uniform(1, 5), 1)}%",
            "perda_por_sujidade": f"{round(random.uniform(1, 6), 1)}%"
        }
        
        # Detalhamento por inversor
        detalhamento_inversores = []
        for inv_id in range(1, 6):  # 5 inversores simulados
            detalhamento_inversores.append({
                "inversor_id": inv_id,
                "eficiencia": round(random.uniform(0.80, 0.95), 4),
                "disponibilidade": round(random.uniform(0.94, 0.999), 4),
                "geracao_total_kwh": round(random.uniform(5000, 8000), 2),
                "horas_operacao": round(random.uniform(2000, 2500), 1),
                "temperatura_media": round(random.uniform(35, 45), 1),
                "estado": random.choice(["Ótimo", "Bom", "Regular", "Requer manutenção"])
            })
        
        # Recomendações de otimização
        recomendacoes = [
            "Limpeza dos painéis dos inversores 2 e 4 para reduzir perdas por sujidade",
            "Verificar sombreamento parcial no setor norte da usina",
            "Agendar manutenção preventiva para o inversor 5",
            "Ajustar ângulo dos painéis para otimizar captação",
            "Avaliar reposicionamento de alguns painéis para reduzir efeito de sombreamento mútuo"
        ]
        
        resultado_final = {
            "usina_id": usina_id,
            "periodo_analise": {
                "inicio": periodo_inicio,
                "fim": periodo_fim
            },
            "metricas_gerais": metricas_gerais,
            "detalhamento_inversores": detalhamento_inversores,
            "recomendacoes": recomendacoes,
            "economia_potencial": f"{round(random.uniform(5, 15), 1)}%"
        }
        
        # Salvar resultado
        arquivo_resultado = salvar_resultado("relatorio_eficiencia", resultado_final, parametros)
        log_processamento(f"Relatório de eficiência concluído com sucesso")
        
        return arquivo_resultado
    
    finally:
        db.close()

def processa_processamento(mensagem):
    """
    Processa uma solicitação de processamento recebida do RabbitMQ
    """
    subtipo = mensagem.get("subtipo")
    parametros = mensagem.get("parametros", {})
    
    log_processamento(f"Iniciando processamento do tipo '{subtipo}'")
    
    try:
        if subtipo == "analise_desempenho":
            return processar_analise_desempenho(parametros)
        elif subtipo == "deteccao_anomalias":
            return processar_deteccao_anomalias(parametros)
        elif subtipo == "previsao_geracao":
            return processar_previsao_geracao(parametros)
        elif subtipo == "relatorio_eficiencia":
            return processar_relatorio_eficiencia(parametros)
        else:
            log_processamento(f"Tipo de processamento não suportado: {subtipo}")
            return None
    except Exception as e:
        log_processamento(f"Erro no processamento '{subtipo}': {str(e)}")
        # Em produção, seria importante gravar logs detalhados do erro
        return None 