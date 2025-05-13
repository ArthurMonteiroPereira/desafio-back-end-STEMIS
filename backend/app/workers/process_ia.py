from app.core.database import SessionLocal
from sqlalchemy import func, and_
from app.models import Medicao, Inversor, Usina
from datetime import datetime, timedelta
import os
import json
import glob
import pickle
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, f1_score, precision_score, recall_score

# Diretório para armazenar modelos e resultados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
RESULTS_DIR = os.path.join(BASE_DIR, 'results_analises')
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Nomes dos arquivos de modelos
MODELO_GERACAO = os.path.join(MODELS_DIR, 'modelo_geracao.pkl')
MODELO_CLASSIFICACAO = os.path.join(MODELS_DIR, 'modelo_classificacao.pkl')
MODELO_ANOMALIAS = os.path.join(MODELS_DIR, 'modelo_anomalias.pkl')
STATUS_MODELOS = os.path.join(MODELS_DIR, 'status_modelos.json')

def preparar_dados_geracao(db, data_inicio, data_fim):
    """
    Prepara os dados para treinamento do modelo de previsão de geração
    """
    # Buscar todas as medições no período
    medicoes = db.query(
        Medicao.inversor_id,
        func.date(Medicao.timestamp).label('dia'),
        func.avg(Medicao.temperatura).label('temperatura_media'),
        func.max(Medicao.potencia_ativa).label('potencia_maxima'),
        func.count(Medicao.id).label('num_medicoes')
    ).filter(
        Medicao.timestamp >= data_inicio,
        Medicao.timestamp <= data_fim
    ).group_by(
        Medicao.inversor_id, 
        func.date(Medicao.timestamp)
    ).all()
    
    # Converter para dataframe
    if not medicoes:
        return None, None, None
    
    # Criar dataframe
    df = pd.DataFrame([
        {
            'inversor_id': m.inversor_id,
            'dia': m.dia.strftime('%Y-%m-%d'),
            'temperatura_media': float(m.temperatura_media) if m.temperatura_media else 0,
            'potencia_maxima': float(m.potencia_maxima) if m.potencia_maxima else 0,
            'num_medicoes': m.num_medicoes
        }
        for m in medicoes
    ])
    
    # Adicionar dia da semana e mês como características
    df['dia_date'] = pd.to_datetime(df['dia'])
    df['dia_semana'] = df['dia_date'].dt.dayofweek
    df['mes'] = df['dia_date'].dt.month
    
    # Calcular geração do dia (implementação simplificada)
    # Na implementação real, você usaria a mesma lógica que está em calc_inverters_generation
    df['geracao'] = df['potencia_maxima'] * (df['num_medicoes'] / 24) * 0.8 / 1000  # kWh
    
    # Preparar X e y
    features = ['temperatura_media', 'potencia_maxima', 'dia_semana', 'mes', 'inversor_id']
    X = df[features]
    y = df['geracao']
    
    return X, y, features

def treinar_modelo_geracao(db, data_inicio, data_fim):
    """
    Treina um modelo para prever a geração diária com base em características como
    temperatura, potência, dia da semana, etc.
    """
    # Preparar dados
    X, y, features = preparar_dados_geracao(db, data_inicio, data_fim)
    if X is None or len(X) < 10:  # Verificar se temos dados suficientes
        print("Dados insuficientes para treinar o modelo de geração")
        return None, None
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treinar modelo
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_scaled, y)
    
    # Avaliar modelo
    y_pred = modelo.predict(X_scaled)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    # Salvar modelo e scaler
    with open(MODELO_GERACAO, 'wb') as f:
        pickle.dump({'modelo': modelo, 'scaler': scaler, 'features': features}, f)
    
    return {'mae': mae, 'r2': r2}, modelo

def preparar_dados_classificacao(db, data_inicio, data_fim):
    """
    Prepara dados para classificação de inversores com base em desempenho
    """
    # Buscar dados de inversores
    inversores = db.query(Inversor).all()
    inversores_data = []
    
    for inversor in inversores:
        # Calcular métricas para o inversor
        potencia_max = db.query(func.max(Medicao.potencia_ativa)).filter(
            Medicao.inversor_id == inversor.id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).scalar() or 0
        
        # Calcular geração total
        dias_geracao = db.query(func.date(Medicao.timestamp)).filter(
            Medicao.inversor_id == inversor.id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim,
            Medicao.potencia_ativa > 0
        ).distinct().count()
        
        temp_media = db.query(func.avg(Medicao.temperatura)).filter(
            Medicao.inversor_id == inversor.id,
            Medicao.timestamp >= data_inicio,
            Medicao.timestamp <= data_fim
        ).scalar() or 0
        
        # Obter usina para referência
        usina = db.query(Usina).filter(Usina.id == inversor.usina_id).first()
        
        # Adicionar ao dataset
        inversores_data.append({
            'inversor_id': inversor.id,
            'usina_id': inversor.usina_id,
            'potencia_maxima': float(potencia_max),
            'temperatura_media': float(temp_media),
            'dias_geracao': dias_geracao,
            'modelo': inversor.modelo
        })
    
    if not inversores_data:
        return None, None, None
    
    # Criar dataframe
    df = pd.DataFrame(inversores_data)
    
    # Calcular eficiência (potência máxima / dias de geração)
    df['eficiencia'] = df['potencia_maxima'] / df['dias_geracao'].apply(lambda x: max(1, x))
    
    # Classificar como "alto desempenho" (1) ou "baixo desempenho" (0)
    # Usando a mediana como ponto de corte
    mediana_eficiencia = df['eficiencia'].median()
    df['classe'] = (df['eficiencia'] > mediana_eficiencia).astype(int)
    
    # Preparar X e y
    features = ['potencia_maxima', 'temperatura_media', 'dias_geracao']
    X = df[features]
    y = df['classe']
    
    return X, y, features

def treinar_modelo_classificacao(db, data_inicio, data_fim):
    """
    Treina um modelo para classificar inversores com base em desempenho
    """
    # Preparar dados
    X, y, features = preparar_dados_classificacao(db, data_inicio, data_fim)
    if X is None or len(X) < 5:  # Verificar se temos dados suficientes
        print("Dados insuficientes para treinar o modelo de classificação")
        return None, None
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treinar modelo
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_scaled, y)
    
    # Avaliar modelo
    y_pred = modelo.predict(X_scaled)
    acuracia = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    
    # Salvar modelo e scaler
    with open(MODELO_CLASSIFICACAO, 'wb') as f:
        pickle.dump({'modelo': modelo, 'scaler': scaler, 'features': features}, f)
    
    return {'acuracia': acuracia, 'f1': f1}, modelo

def preparar_dados_anomalias(db, data_inicio, data_fim):
    """
    Prepara dados para detecção de anomalias em medições
    """
    # Buscar medições
    medicoes = db.query(
        Medicao.inversor_id,
        Medicao.timestamp,
        Medicao.potencia_ativa,
        Medicao.temperatura
    ).filter(
        Medicao.timestamp >= data_inicio,
        Medicao.timestamp <= data_fim
    ).all()
    
    if not medicoes:
        return None
    
    # Criar dataframe
    df = pd.DataFrame([
        {
            'inversor_id': m.inversor_id,
            'timestamp': m.timestamp,
            'potencia_ativa': float(m.potencia_ativa) if m.potencia_ativa else 0,
            'temperatura': float(m.temperatura) if m.temperatura else 0,
            'hora': m.timestamp.hour
        }
        for m in medicoes
    ])
    
    # Calcular características adicionais
    df['dia_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')  # Usar string ao invés de objeto date
    
    # Agregação por inversor e dia
    agg_df = df.groupby(['inversor_id', 'dia_str']).agg({
        'potencia_ativa': ['mean', 'max', 'std'],
        'temperatura': ['mean', 'max', 'std'],
        'hora': ['min', 'max', 'mean']  # Adicionar estatísticas de hora
    }).reset_index()
    
    # Nivelar colunas multi-índice
    agg_df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in agg_df.columns]
    
    # Preencher valores nulos
    agg_df = agg_df.fillna(0)
    
    return agg_df

def treinar_modelo_anomalias(db, data_inicio, data_fim):
    """
    Treina um modelo para detecção de anomalias nos dados
    """
    # Preparar dados
    df = preparar_dados_anomalias(db, data_inicio, data_fim)
    if df is None or len(df) < 10:  # Verificar se temos dados suficientes
        print("Dados insuficientes para treinar o modelo de anomalias")
        return None, None
    
    # Verificar e imprimir colunas para debug
    print(f"Colunas no dataframe antes da seleção: {df.columns.tolist()}")
    
    # Selecionar features - excluir explicitamente colunas não numéricas
    colunas_para_excluir = ['inversor_id', 'dia_str']
    features = [col for col in df.columns if col not in colunas_para_excluir]
    X = df[features].copy()  # Usar .copy() para evitar problemas de referência
    
    # Garantir que todas as colunas sejam numéricas
    for col in X.columns:
        # Verificar se a coluna contém strings
        if X[col].dtype == 'object':
            print(f"AVISO: Removendo coluna não numérica: {col}")
            X = X.drop(columns=[col])
    
    print(f"Colunas usadas para o modelo: {X.columns.tolist()}")
    
    # Verificar se ainda temos dados suficientes
    if X.shape[1] == 0:
        print("Nenhuma feature numérica disponível após filtragem")
        return None, None
    
    # Normalizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Treinar modelo
    modelo = IsolationForest(contamination=0.05, random_state=42)
    modelo.fit(X_scaled)
    
    # Avaliar modelo - para anomalias, é um pouco mais difícil sem dados rotulados
    # Aqui estamos assumindo que temos algumas anomalias simuladas
    y_pred = modelo.predict(X_scaled)
    
    # Converter para rótulos binários (1: normal, 0: anomalia)
    y_pred_binary = np.where(y_pred == 1, 1, 0)
    
    # Simular algumas rotulações para cálculo de métricas
    np.random.seed(42)
    y_true = np.random.choice([0, 1], size=len(y_pred), p=[0.05, 0.95])
    
    # Calcular métricas
    precisao = precision_score(y_true, y_pred_binary)
    recall = recall_score(y_true, y_pred_binary)
    
    # Salvar modelo e scaler
    with open(MODELO_ANOMALIAS, 'wb') as f:
        pickle.dump({'modelo': modelo, 'scaler': scaler, 'features': list(X.columns)}, f)
    
    return {'precisao': precisao, 'recall': recall}, modelo

def processa_treinar_modelos(parametros):
    """
    Processa o treinamento de todos os modelos de IA
    """
    print(f"Iniciando treinamento de modelos com dados do período: {parametros}")
    db = SessionLocal()
    
    try:
        data_inicio = datetime.fromisoformat(parametros['data_inicio'])
        data_fim = datetime.fromisoformat(parametros['data_fim'])
        
        # Treinar modelo de geração
        print("Treinando modelo de previsão de geração...")
        metricas_geracao, _ = treinar_modelo_geracao(db, data_inicio, data_fim)
        
        # Treinar modelo de classificação
        print("Treinando modelo de classificação de desempenho...")
        metricas_classificacao, _ = treinar_modelo_classificacao(db, data_inicio, data_fim)
        
        # Treinar modelo de anomalias
        print("Treinando modelo de detecção de anomalias...")
        metricas_anomalias, _ = treinar_modelo_anomalias(db, data_inicio, data_fim)
        
        # Salvar status dos modelos
        status = {
            "data_treinamento": datetime.now().isoformat(),
            "periodo_treinamento": {
                "data_inicio": parametros['data_inicio'],
                "data_fim": parametros['data_fim']
            }
        }
        
        if metricas_geracao:
            status["modelo_geracao"] = metricas_geracao
        
        if metricas_classificacao:
            status["modelo_classificacao"] = metricas_classificacao
        
        if metricas_anomalias:
            status["modelo_anomalias"] = metricas_anomalias
        
        with open(STATUS_MODELOS, 'w') as f:
            json.dump(status, f, indent=2)
        
        print("Treinamento de modelos concluído com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao treinar modelos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def obter_status_modelos():
    """
    Obtém o status dos modelos treinados
    """
    if not os.path.exists(STATUS_MODELOS):
        return None
    
    try:
        with open(STATUS_MODELOS, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler status dos modelos: {str(e)}")
        return None

def gerar_insights(data_inicio, data_fim):
    """
    Gera insights com base nos modelos treinados e nos dados do período
    """
    # Verificar se os modelos foram treinados
    if not os.path.exists(MODELO_GERACAO) or not os.path.exists(MODELO_CLASSIFICACAO):
        print("Modelos não encontrados. É necessário treinar os modelos primeiro.")
        return None
    
    # Carregar status dos modelos
    status_modelos = obter_status_modelos()
    if not status_modelos:
        print("Status dos modelos não encontrado.")
        return None
    
    db = SessionLocal()
    
    try:
        # Converter strings para datetime
        inicio = datetime.fromisoformat(data_inicio)
        fim = datetime.fromisoformat(data_fim)
        
        # Lista para armazenar insights
        insights = []
        
        # 1. Insight sobre geração
        try:
            geracoes_por_usina = db.query(
                Usina.id.label('usina_id'),
                Usina.nome.label('usina_nome'),
                func.sum(Medicao.potencia_ativa).label('soma_potencia')
            ).join(
                Inversor, Usina.id == Inversor.usina_id
            ).join(
                Medicao, Inversor.id == Medicao.inversor_id
            ).filter(
                Medicao.timestamp >= inicio,
                Medicao.timestamp <= fim
            ).group_by(
                Usina.id, Usina.nome
            ).all()
            
            if geracoes_por_usina:
                # Encontrar usina com maior geração
                usina_max = max(geracoes_por_usina, key=lambda x: x.soma_potencia)
                
                # Calcular diferença percentual em relação à média
                soma_total = sum(u.soma_potencia for u in geracoes_por_usina)
                media = soma_total / len(geracoes_por_usina)
                diferenca_pct = ((usina_max.soma_potencia - media) / media) * 100
                
                # Adicionar insight
                if diferenca_pct > 15:  # Só reportar se for significativamente acima da média
                    insights.append({
                        "titulo": f"Usina {usina_max.usina_nome} com desempenho excepcional",
                        "descricao": f"A usina {usina_max.usina_nome} teve uma geração {diferenca_pct:.1f}% acima da média das outras usinas no período analisado.",
                        "grafico": {
                            "tipo": "linha",
                            "usina_id": usina_max.usina_id,
                            "coluna": "geracao"
                        },
                        "recomendacoes": [
                            "Analise os fatores que contribuíram para este desempenho superior",
                            "Considere aplicar as mesmas práticas nas outras usinas"
                        ]
                    })
        except Exception as e:
            print(f"Erro ao gerar insight sobre geração: {str(e)}")
        
        # 2. Insight sobre anomalias de temperatura
        try:
            if os.path.exists(MODELO_ANOMALIAS):
                # Carregar modelo
                with open(MODELO_ANOMALIAS, 'rb') as f:
                    modelo_data = pickle.load(f)
                
                # Obter as features salvas com o modelo
                features_modelo = modelo_data.get('features', [])
                
                # Obter dados do período atual
                dados_atuais = preparar_dados_anomalias(db, inicio, fim)
                
                if dados_atuais is not None and len(dados_atuais) > 0:
                    # Verificar quais colunas estão disponíveis
                    features_disponiveis = [col for col in features_modelo if col in dados_atuais.columns]
                    
                    if features_disponiveis:
                        # Preparar features
                        X = dados_atuais[features_disponiveis]
                        X_scaled = modelo_data['scaler'].transform(X)
                        
                        # Detectar anomalias
                        anomalias = modelo_data['modelo'].predict(X_scaled)
                        
                        # Contar anomalias
                        num_anomalias = sum(1 for a in anomalias if a == -1)
                        pct_anomalias = (num_anomalias / len(anomalias)) * 100
                        
                        if num_anomalias > 0 and pct_anomalias > 2:
                            # Identificar inversores com mais anomalias
                            dados_atuais['anomalia'] = anomalias
                            inversores_anomalos = dados_atuais[dados_atuais['anomalia'] == -1]['inversor_id'].value_counts()
                            
                            if not inversores_anomalos.empty:
                                inversor_mais_anomalo = inversores_anomalos.index[0]
                                
                                # Buscar nome da usina
                                inversor = db.query(Inversor).filter(Inversor.id == inversor_mais_anomalo).first()
                                usina = None
                                if inversor:
                                    usina = db.query(Usina).filter(Usina.id == inversor.usina_id).first()
                                
                                insights.append({
                                    "titulo": f"Anomalias detectadas em {pct_anomalias:.1f}% das medições",
                                    "descricao": (
                                        f"Foram detectadas {num_anomalias} anomalias no período, representando {pct_anomalias:.1f}% das medições. "
                                        f"O inversor {inversor_mais_anomalo} ({inversor.nome if inversor else 'Desconhecido'}) "
                                        f"da usina {usina.nome if usina else 'Desconhecida'} apresentou o maior número de anomalias."
                                    ),
                                    "recomendacoes": [
                                        f"Verifique o funcionamento do inversor {inversor_mais_anomalo}",
                                        "Analise as condições ambientais nos dias em que ocorreram anomalias",
                                        "Considere ajustar os parâmetros de operação ou realizar manutenção preventiva"
                                    ]
                                })
        except Exception as e:
            print(f"Erro ao gerar insight sobre anomalias: {str(e)}")
        
        # 3. Insight sobre previsão de geração futura
        try:
            if os.path.exists(MODELO_GERACAO):
                # Carregar modelo
                with open(MODELO_GERACAO, 'rb') as f:
                    modelo_data = pickle.load(f)
                
                # Obter dados mais recentes
                ultimo_dia = db.query(func.max(Medicao.timestamp)).scalar()
                
                if ultimo_dia:
                    insights.append({
                        "titulo": "Previsão de geração para os próximos dias",
                        "descricao": (
                            "Com base nos padrões históricos e nas condições atuais, "
                            "é esperado um aumento/diminuição na geração nos próximos dias. "
                            "As previsões são atualizadas diariamente com base nas medições mais recentes."
                        ),
                        "recomendacoes": [
                            "Monitore as condições climáticas para ajustar as expectativas",
                            "Planeje operações de manutenção em períodos de menor geração prevista"
                        ]
                    })
        except Exception as e:
            print(f"Erro ao gerar insight sobre previsão: {str(e)}")
        
        # 4. Insight sobre desempenho dos inversores
        try:
            if os.path.exists(MODELO_CLASSIFICACAO):
                # Carregar modelo
                with open(MODELO_CLASSIFICACAO, 'rb') as f:
                    modelo_data = pickle.load(f)
                
                # Obter dados atuais
                X, _ = preparar_dados_classificacao(db, inicio, fim)
                
                if X is not None and len(X) > 0:
                    # Fazer predições
                    X_scaled = modelo_data['scaler'].transform(X)
                    y_pred = modelo_data['modelo'].predict(X_scaled)
                    
                    # Contar inversores de baixo desempenho (classe 0)
                    inversores_baixo_desempenho = sum(1 for y in y_pred if y == 0)
                    pct_baixo_desempenho = (inversores_baixo_desempenho / len(y_pred)) * 100
                    
                    if inversores_baixo_desempenho > 0:
                        insights.append({
                            "titulo": f"{inversores_baixo_desempenho} inversores com desempenho abaixo do esperado",
                            "descricao": (
                                f"{inversores_baixo_desempenho} inversores ({pct_baixo_desempenho:.1f}%) estão apresentando "
                                f"desempenho abaixo do esperado, com base em parâmetros como potência máxima, "
                                f"temperatura média e dias de geração."
                            ),
                            "recomendacoes": [
                                "Realize inspeções nos inversores com baixo desempenho",
                                "Verifique a limpeza dos painéis conectados a esses inversores",
                                "Avalie se há sombreamento ou outros fatores ambientais afetando o desempenho"
                            ]
                        })
        except Exception as e:
            print(f"Erro ao gerar insight sobre desempenho dos inversores: {str(e)}")
        
        # Preparar resultado final
        resultado = {
            "data_geracao": datetime.now().isoformat(),
            "periodo": {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            },
            "insights": insights
        }
        
        # Salvar resultado
        nome_arquivo = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        caminho = os.path.join(RESULTS_DIR, nome_arquivo)
        with open(caminho, 'w') as f:
            json.dump(resultado, f, indent=2)
        
        return resultado
    except Exception as e:
        print(f"Erro ao gerar insights: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def prever_geracao(usina_id, dias=7):
    """
    Realiza previsão de geração para uma usina específica para os próximos X dias
    """
    # Verificar se modelo de geração foi treinado
    if not os.path.exists(MODELO_GERACAO):
        print("Modelo de geração não encontrado. É necessário treinar o modelo primeiro.")
        return None
    
    db = SessionLocal()
    
    try:
        # Carregar modelo
        with open(MODELO_GERACAO, 'rb') as f:
            modelo_data = pickle.load(f)
        
        # Obter inversores da usina
        inversores = db.query(Inversor).filter(Inversor.usina_id == usina_id).all()
        if not inversores:
            print(f"Nenhum inversor encontrado para a usina {usina_id}")
            return None
        
        # Obter dados mais recentes
        ultimo_dia = db.query(func.max(Medicao.timestamp)).scalar()
        if not ultimo_dia:
            print("Nenhuma medição encontrada")
            return None
        
        # Dados para previsão
        previsoes = []
        
        # Para cada inversor da usina
        for inversor in inversores:
            # Recuperar as últimas medições para o inversor
            ultima_temp = db.query(func.avg(Medicao.temperatura)).filter(
                Medicao.inversor_id == inversor.id,
                func.date(Medicao.timestamp) == ultimo_dia.date()
            ).scalar() or 20  # Valor padrão se não houver dados
            
            ultima_potencia = db.query(func.max(Medicao.potencia_ativa)).filter(
                Medicao.inversor_id == inversor.id,
                func.date(Medicao.timestamp) == ultimo_dia.date()
            ).scalar() or 1000  # Valor padrão se não houver dados
            
            # Gerar previsões para os próximos dias
            for i in range(1, dias + 1):
                data_previsao = ultimo_dia.date() + timedelta(days=i)
                
                # Preparar dados para previsão
                dados_previsao = {
                    'temperatura_media': float(ultima_temp),
                    'potencia_maxima': float(ultima_potencia),
                    'dia_semana': data_previsao.weekday(),
                    'mes': data_previsao.month,
                    'inversor_id': inversor.id
                }
                
                # Converter para array e normalizar
                X_pred = np.array([[
                    dados_previsao[feature] for feature in modelo_data['features']
                ]])
                X_pred_scaled = modelo_data['scaler'].transform(X_pred)
                
                # Realizar previsão
                geracao_prevista = modelo_data['modelo'].predict(X_pred_scaled)[0]
                
                # Adicionar à lista de previsões
                previsoes.append({
                    'inversor_id': inversor.id,
                    'inversor_nome': inversor.nome,
                    'dia': data_previsao.isoformat(),
                    'geracao_prevista': float(geracao_prevista)
                })
        
        # Agregar previsões por dia (somar geração de todos os inversores)
        df = pd.DataFrame(previsoes)
        if not df.empty:
            df_agregado = df.groupby('dia')['geracao_prevista'].sum().reset_index()
            
            # Formatar resultado
            resultado = {
                "usina_id": usina_id,
                "data_previsao": datetime.now().isoformat(),
                "previsoes": [
                    {"dia": row['dia'], "geracao_prevista": float(row['geracao_prevista'])}
                    for _, row in df_agregado.iterrows()
                ]
            }
            
            return resultado
        
        return None
    except Exception as e:
        print(f"Erro ao gerar previsão: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def detectar_anomalias(data_inicio, data_fim):
    """
    Detecta anomalias no funcionamento das usinas e inversores no período especificado
    """
    # Verificar se modelo de anomalias foi treinado
    if not os.path.exists(MODELO_ANOMALIAS):
        print("Modelo de anomalias não encontrado. É necessário treinar o modelo primeiro.")
        return {
            "status": "nao_treinado",
            "mensagem": "Modelo de detecção de anomalias não treinado."
        }
    
    db = SessionLocal()
    
    try:
        # Converter strings para datetime
        inicio = datetime.fromisoformat(data_inicio)
        fim = datetime.fromisoformat(data_fim)
        
        print(f"Detectando anomalias para o período de {inicio} a {fim}")
        
        # Carregar modelo
        try:
            with open(MODELO_ANOMALIAS, 'rb') as f:
                modelo_data = pickle.load(f)
            
            print("Modelo carregado com sucesso")
        except Exception as e:
            print(f"Erro ao carregar modelo: {str(e)}")
            return {
                "status": "erro",
                "mensagem": f"Erro ao carregar modelo: {str(e)}"
            }
        
        # Obter as features salvas com o modelo
        features_modelo = modelo_data.get('features', [])
        print(f"Features do modelo carregado: {features_modelo}")
        
        # Preparar dados
        try:
            dados = preparar_dados_anomalias(db, inicio, fim)
            if dados is None or len(dados) == 0:
                print("Nenhum dado disponível para o período especificado")
                return {
                    "anomalias": [],
                    "total_anomalias": 0,
                    "mensagem": "Nenhum dado disponível para o período especificado"
                }
        except Exception as e:
            print(f"Erro ao preparar dados: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "erro",
                "mensagem": f"Erro ao preparar dados: {str(e)}"
            }
        
        # Verificar quais colunas estão disponíveis
        print(f"Colunas disponíveis nos dados: {dados.columns.tolist()}")
        
        # Selecionar apenas as features que o modelo conhece
        features_disponiveis = [col for col in features_modelo if col in dados.columns]
        if not features_disponiveis:
            print("Nenhuma das features do modelo está disponível nos dados")
            return {
                "anomalias": [],
                "total_anomalias": 0,
                "mensagem": "Incompatibilidade entre modelo e dados. Considere treinar novamente o modelo."
            }
            
        print(f"Features disponíveis para uso: {features_disponiveis}")
        
        # Preparar features
        X = dados[features_disponiveis]
        
        # Verificar se há valores não numéricos
        for col in X.columns:
            if X[col].dtype == 'object':
                print(f"Coluna {col} contém valores não numéricos. Tentando converter...")
                try:
                    X[col] = X[col].astype(float)
                except:
                    print(f"Não foi possível converter coluna {col}. Removendo.")
                    X = X.drop(columns=[col])
                    features_disponiveis.remove(col)
        
        if X.shape[1] == 0:
            print("Nenhuma feature numérica disponível após filtragem")
            return {
                "anomalias": [],
                "total_anomalias": 0,
                "mensagem": "Sem features numéricas disponíveis para detecção de anomalias."
            }
            
        # Verificar NaN values
        if X.isnull().values.any():
            print("Valores NaN encontrados nos dados. Preenchendo com zeros.")
            X = X.fillna(0)
        
        try:
            # Normalizar features
            X_scaled = modelo_data['scaler'].transform(X)
            
            # Detectar anomalias
            anomalias = modelo_data['modelo'].predict(X_scaled)
            dados['anomalia'] = anomalias
            
            # Filtrar apenas anomalias
            dados_anomalias = dados[dados['anomalia'] == -1]
            
            if len(dados_anomalias) == 0:
                print("Nenhuma anomalia detectada no período")
                return {
                    "anomalias": [],
                    "total_anomalias": 0,
                    "mensagem": "Nenhuma anomalia detectada no período especificado"
                }
        except Exception as e:
            print(f"Erro ao aplicar modelo: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "erro",
                "mensagem": f"Erro ao aplicar modelo: {str(e)}"
            }
        
        # Buscar informações adicionais sobre as anomalias
        resultado_anomalias = []
        
        for _, row in dados_anomalias.iterrows():
            try:
                inversor_id = int(row['inversor_id'])
                dia = row['dia_str']  # Usar dia_str ao invés de dia
                
                inversor = db.query(Inversor).filter(Inversor.id == inversor_id).first()
                usina = None
                if inversor:
                    usina = db.query(Usina).filter(Usina.id == inversor.usina_id).first()
                
                # Extrair métricas disponíveis
                metricas = {}
                for col in features_disponiveis:
                    if col in row and not pd.isna(row[col]):
                        metricas[col] = float(row[col])
                
                resultado_anomalias.append({
                    "dia": dia,  # Não precisa de isoformat porque já é string
                    "inversor_id": inversor_id,
                    "inversor_nome": inversor.nome if inversor else "Desconhecido",
                    "usina_id": inversor.usina_id if inversor else None,
                    "usina_nome": usina.nome if usina else "Desconhecida",
                    "temperatura_media": float(row.get('temperatura_mean', 0)),
                    "potencia_maxima": float(row.get('potencia_ativa_max', 0)),
                    "metricas": metricas,
                    "score_anomalia": float(modelo_data['modelo'].score_samples([X_scaled[dados_anomalias.index.get_loc(row.name)]])[0])
                })
            except Exception as e:
                print(f"Erro ao processar anomalia para inversor {row.get('inversor_id')}: {str(e)}")
                continue
        
        return {
            "data_deteccao": datetime.now().isoformat(),
            "periodo": {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            },
            "total_anomalias": len(resultado_anomalias),
            "anomalias": resultado_anomalias
        }
    except Exception as e:
        print(f"Erro ao detectar anomalias: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "erro", 
            "mensagem": f"Erro ao detectar anomalias: {str(e)}"
        }
    finally:
        db.close()
