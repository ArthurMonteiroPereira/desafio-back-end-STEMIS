import streamlit as st
import requests
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time

API_URL = "http://localhost:8000"

def obter_status_modelos():
    """
    Obtém o status dos modelos treinados (data do último treinamento, métricas, etc.)
    """
    try:
        resp = requests.get(f"{API_URL}/ia/status")
        if resp.ok:
            return resp.json()
        elif resp.status_code == 404:
            return {"status": "nao_treinado", "mensagem": "Nenhum modelo treinado encontrado."}
        else:
            st.error(f"Erro ao obter status dos modelos: {resp.text}")
            return {"status": "erro", "mensagem": f"Erro ao obter status: {resp.text}"}
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return {"status": "erro", "mensagem": f"Erro de conexão: {str(e)}"}

def solicitar_treinamento(data_inicio, data_fim):
    """
    Solicita o treinamento de novos modelos com base no período especificado
    """
    try:
        payload = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
        resp = requests.post(f"{API_URL}/ia/treinar", json=payload)
        if resp.ok:
            return resp.json().get("msg", "Solicitação de treinamento enviada.")
        else:
            return f"Erro: {resp.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"

def obter_insights(data_inicio, data_fim):
    """
    Obtém insights gerados pelos modelos para o período especificado
    """
    try:
        params = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
        resp = requests.get(f"{API_URL}/ia/insights", params=params)
        if resp.ok:
            return resp.json()
        elif resp.status_code == 404:
            return {"status": "nao_encontrado", "mensagem": "Insights não disponíveis para o período."}
        else:
            st.error(f"Erro ao obter insights: {resp.text}")
            return {"status": "erro", "mensagem": f"Erro ao obter insights: {resp.text}"}
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return {"status": "erro", "mensagem": f"Erro de conexão: {str(e)}"}

def detectar_anomalias(data_inicio, data_fim):
    """
    Solicita a detecção de anomalias no período especificado.
    """
    try:
        params = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
        resp = requests.get(f"{API_URL}/ia/anomalias", params=params)
        if resp.ok:
            return resp.json()
        elif resp.status_code == 404:
            return {"anomalias": [], "mensagem": "Nenhuma anomalia detectada no período."}
        else:
            st.error(f"Erro ao detectar anomalias: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def obter_previsao_geracao(usina_id, dias=7):
    """
    Obtém previsão de geração para uma usina específica.
    """
    try:
        params = {
            "usina_id": usina_id,
            "dias": dias
        }
        resp = requests.get(f"{API_URL}/ia/previsao/geracao", params=params)
        if resp.ok:
            return resp.json()
        elif resp.status_code == 404:
            return {"status": "nao_encontrado", "mensagem": f"Previsão indisponível para usina {usina_id}"}
        else:
            st.error(f"Erro ao obter previsão: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def obter_usinas():
    """
    Obtém lista de usinas para seleção.
    """
    try:
        resp = requests.get(f"{API_URL}/usinas/")
        if resp.ok:
            return resp.json()
        else:
            st.error(f"Erro ao obter usinas: {resp.text}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

def exibir_metricas_modelos(status_modelos):
    """
    Exibe as métricas de desempenho dos modelos treinados
    """
    if status_modelos.get("status") == "nao_treinado" or status_modelos.get("status") == "erro":
        st.warning(status_modelos.get("mensagem", "Status dos modelos não disponível."))
        return
    
    st.subheader("Métricas dos Modelos")
    
    # Exibir métricas em tabs
    if "modelo_geracao" in status_modelos or "modelo_classificacao" in status_modelos or "modelo_anomalias" in status_modelos:
        tab1, tab2, tab3 = st.tabs(["Modelo de Geração", "Modelo de Classificação", "Modelo de Anomalias"])
        
        with tab1:
            if "modelo_geracao" in status_modelos:
                metricas = status_modelos["modelo_geracao"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("MAE (Mean Absolute Error)", f"{metricas.get('mae', 0):.4f}")
                with col2:
                    st.metric("R² (Coeficiente de Determinação)", f"{metricas.get('r2', 0):.4f}")
                
                # Exibir importância das features se disponível
                if "feature_importance" in metricas:
                    st.subheader("Importância das Features")
                    fi = metricas["feature_importance"]
                    fig = px.bar(
                        x=list(fi.keys()), 
                        y=list(fi.values()),
                        labels={'x': 'Feature', 'y': 'Importância'},
                        title="Importância Relativa das Features"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Modelo de geração não treinado.")
        
        with tab2:
            if "modelo_classificacao" in status_modelos:
                metricas = status_modelos["modelo_classificacao"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Acurácia", f"{metricas.get('acuracia', 0):.4f}")
                with col2:
                    st.metric("F1-Score", f"{metricas.get('f1', 0):.4f}")
                
                # Exibir matriz de confusão se disponível
                if "matriz_confusao" in metricas:
                    st.subheader("Matriz de Confusão")
                    matriz = metricas["matriz_confusao"]
                    fig = px.imshow(
                        matriz,
                        labels=dict(x="Previsto", y="Real", color="Contagem"),
                        x=["Baixo Desemp.", "Alto Desemp."],
                        y=["Baixo Desemp.", "Alto Desemp."],
                        text_auto=True,
                        aspect="equal",
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Modelo de classificação não treinado.")
        
        with tab3:
            if "modelo_anomalias" in status_modelos:
                metricas = status_modelos["modelo_anomalias"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Precisão", f"{metricas.get('precisao', 0):.4f}")
                with col2:
                    st.metric("Recall", f"{metricas.get('recall', 0):.4f}")
                
                # Exibir distribuição de scores se disponível
                if "distribuicao_scores" in metricas:
                    st.subheader("Distribuição de Scores de Anomalia")
                    scores = metricas["distribuicao_scores"]
                    fig = px.histogram(
                        scores,
                        nbins=20,
                        labels={"value": "Score de Anomalia", "count": "Frequência"},
                        title="Distribuição dos Scores de Anomalia"
                    )
                    fig.add_vline(x=metricas.get("threshold", 0), line_dash="dash", line_color="red")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Modelo de detecção de anomalias não treinado.")

def exibir_insights(insights, dashboard_data=None):
    """
    Exibe os insights gerados pelos modelos de IA
    """
    if insights.get("status") == "nao_encontrado" or insights.get("status") == "erro":
        st.warning(insights.get("mensagem", "Insights não disponíveis."))
        return False
    
    insights_list = insights.get("insights", [])
    if not insights_list:
        st.info("Nenhum insight significativo encontrado para o período.")
        return False
    
    st.subheader(f"Insights Gerados ({len(insights_list)})")
    
    # Exibir cada insight como um card expansível
    for i, insight in enumerate(insights_list):
        with st.expander(f"{i+1}. {insight.get('titulo', 'Insight')}", expanded=i==0):
            st.markdown(f"**{insight.get('descricao', '')}**")
            
            # Se houver gráfico, exibir
            if "grafico" in insight and dashboard_data:
                tipo_grafico = insight.get("grafico", {}).get("tipo")
                if tipo_grafico == "linha":
                    # Extrair dados para o gráfico de linha
                    if "usina_id" in insight.get("grafico", {}):
                        usina_id = insight["grafico"]["usina_id"]
                        serie_temporal = dashboard_data.get("serie_temporal_usinas", {}).get(str(usina_id), [])
                        
                        if serie_temporal:
                            # Criar dataframe para o gráfico
                            df = pd.DataFrame(serie_temporal)
                            df['dia'] = pd.to_datetime(df['dia'])
                            
                            # Criar gráfico com plotly
                            coluna = insight["grafico"]["coluna"]
                            fig = px.line(
                                df, x='dia', y=coluna,
                                title=f"Série Temporal - {coluna.capitalize()}",
                                labels={'dia': 'Data', coluna: coluna.capitalize()},
                                markers=True
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            # Se houver recomendações, exibir
            if "recomendacoes" in insight:
                st.markdown("### Recomendações:")
                for rec in insight["recomendacoes"]:
                    st.markdown(f"- {rec}")
    
    return True

def exibir_previsao_geracao():
    """
    Exibe previsão de geração para usinas.
    """
    st.subheader("Previsão de Geração")
    
    # Obter usinas
    usinas = obter_usinas()
    if not usinas:
        st.warning("Não foi possível obter a lista de usinas.")
        return
    
    # Seleção de usina
    opcoes_usina = {u["nome"]: u["id"] for u in usinas}
    usina_selecionada = st.selectbox("Selecione a Usina", options=list(opcoes_usina.keys()))
    usina_id = opcoes_usina[usina_selecionada]
    
    # Seleção de dias para previsão
    dias = st.slider("Dias para previsão", 1, 30, 7)
    
    if st.button("Gerar Previsão"):
        with st.spinner(f"Gerando previsão para {usina_selecionada} para os próximos {dias} dias..."):
            previsao = obter_previsao_geracao(usina_id, dias)
        
        if not previsao or previsao.get("status") == "nao_encontrado":
            st.warning(f"Não foi possível gerar previsão para a usina {usina_selecionada}.")
            st.info("Certifique-se de que os modelos estão treinados.")
            return
        
        # Exibir informações gerais
        st.success(f"Previsão gerada com sucesso para {usina_selecionada}!")
        
        # Exibir gráfico de previsão
        previsoes = previsao.get("previsoes", [])
        if previsoes:
            df_previsao = pd.DataFrame(previsoes)
            df_previsao["dia"] = pd.to_datetime(df_previsao["dia"])
            
            # Criar gráfico com plotly
            fig = px.line(
                df_previsao, 
                x="dia", 
                y="geracao_prevista", 
                title=f"Previsão de Geração para {usina_selecionada} - Próximos {dias} dias",
                labels={"dia": "Data", "geracao_prevista": "Geração Prevista (kWh)"},
                markers=True
            )
            
            # Personalizar gráfico
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title="Geração Prevista (kWh)",
                hovermode="x unified"
            )
            
            # Exibir gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir tabela de dados
            st.dataframe(
                df_previsao.rename(columns={
                    "dia": "Data", 
                    "geracao_prevista": "Geração Prevista (kWh)"
                }).set_index("Data")
            )
            
            # Exibir estatísticas
            total_previsto = previsao.get("geracao_total_prevista", sum(p.get("geracao_prevista", 0) for p in previsoes))
            media_diaria = total_previsto / len(previsoes)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Geração Total Prevista (kWh)", f"{total_previsto:.2f}")
            with col2:
                st.metric("Média Diária Prevista (kWh/dia)", f"{media_diaria:.2f}")
        else:
            st.info("Não há dados suficientes para exibir a previsão.")

def exibir_deteccao_anomalias():
    """
    Exibe detecção de anomalias para o período selecionado.
    """
    st.subheader("Detecção de Anomalias")
    
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data início para anomalias", value=date.today() - timedelta(days=30))
    with col2:
        data_fim = st.date_input("Data fim para anomalias", value=date.today())
    
    if st.button("Detectar Anomalias"):
        # Converter para string ISO
        data_inicio_str = data_inicio.isoformat()
        data_fim_str = data_fim.isoformat()
        
        with st.spinner("Detectando anomalias..."):
            resultado = detectar_anomalias(data_inicio_str, data_fim_str)
        
        if not resultado:
            st.warning("Não foi possível realizar a detecção de anomalias.")
            st.info("Certifique-se de que os modelos estão treinados.")
            return
        
        anomalias = resultado.get("anomalias", [])
        total_anomalias = resultado.get("total_anomalias", len(anomalias))
        
        if total_anomalias == 0:
            st.success("Nenhuma anomalia detectada no período selecionado!")
            return
        
        # Exibir resumo
        st.warning(f"Foram detectadas {total_anomalias} anomalias no período selecionado")
        
        # Criar dataframe para análise
        if anomalias:
            df_anomalias = pd.DataFrame(anomalias)
            
            # Formatar colunas
            colunas_formatadas = {
                "dia": "Data",
                "inversor_id": "ID do Inversor",
                "inversor_nome": "Inversor",
                "usina_id": "ID da Usina",
                "usina_nome": "Usina",
                "temperatura_media": "Temperatura Média (°C)",
                "potencia_maxima": "Potência Máxima (W)",
                "score_anomalia": "Score de Anomalia"
            }
            
            df_display = df_anomalias.rename(columns={k: v for k, v in colunas_formatadas.items() if k in df_anomalias.columns})
            
            # Exibir tabela
            st.dataframe(df_display)
            
            # Agrupar anomalias por usina/inversor
            if "usina_nome" in df_anomalias.columns and "inversor_nome" in df_anomalias.columns:
                # Contagem por usina
                st.subheader("Anomalias por Usina")
                contagem_usina = df_anomalias["usina_nome"].value_counts().reset_index()
                contagem_usina.columns = ["Usina", "Quantidade de Anomalias"]
                
                # Criar gráfico
                fig = px.bar(
                    contagem_usina, 
                    x="Usina", 
                    y="Quantidade de Anomalias",
                    title="Distribuição de Anomalias por Usina"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Contagem por inversor
                st.subheader("Anomalias por Inversor")
                contagem_inversor = df_anomalias["inversor_nome"].value_counts().reset_index()
                contagem_inversor.columns = ["Inversor", "Quantidade de Anomalias"]
                
                # Criar gráfico
                fig = px.bar(
                    contagem_inversor, 
                    x="Inversor", 
                    y="Quantidade de Anomalias",
                    title="Distribuição de Anomalias por Inversor",
                    color="Quantidade de Anomalias",
                    color_continuous_scale=["green", "yellow", "red"]
                )
                st.plotly_chart(fig, use_container_width=True)

def render_dashboard_ia():
    st.title("Dashboard IA - Insights e Previsões")
    
    # Criar menu de navegação
    opcoes_menu = ["Status dos Modelos", "Previsão de Geração", "Detecção de Anomalias", "Insights"]
    selecao = st.radio("Navegação", opcoes_menu)
    
    # Exibir status dos modelos
    if selecao == "Status dos Modelos":
        status_modelos = obter_status_modelos()
        
        # Cabeçalho com informações sobre o último treinamento
        if "data_treinamento" in status_modelos:
            try:
                data_formatada = datetime.fromisoformat(status_modelos["data_treinamento"]).strftime("%d/%m/%Y %H:%M:%S")
                st.info(f"Modelos treinados em: {data_formatada}")
            except:
                st.info(f"Modelos treinados em: {status_modelos.get('data_treinamento')}")
            
            # Período do treinamento
            periodo = status_modelos.get("periodo_treinamento", {})
            if periodo:
                st.info(f"Período utilizado: {periodo.get('data_inicio')} a {periodo.get('data_fim')}")
        elif status_modelos.get("status") == "nao_treinado":
            st.warning("Nenhum modelo treinado encontrado. Utilize o formulário abaixo para treinar novos modelos.")
        
        # Exibir métricas dos modelos (se disponíveis)
        if status_modelos.get("status") != "nao_treinado":
            exibir_metricas_modelos(status_modelos)
        
        st.markdown("---")
        
        # Formulário para treinamento de novos modelos
        st.subheader("Treinar Novos Modelos")
        with st.form("form_treinar_modelos"):
            col1, col2 = st.columns(2)
            with col1:
                data_inicio_treino = st.date_input("Data início para treinamento", 
                                                value=date.today() - timedelta(days=60))
            with col2:
                data_fim_treino = st.date_input("Data fim para treinamento", 
                                              value=date.today())
            
            submitted = st.form_submit_button("Treinar Modelos")
            if submitted:
                with st.spinner("Solicitando treinamento de modelos..."):
                    msg = solicitar_treinamento(data_inicio_treino.isoformat(), data_fim_treino.isoformat())
                    st.success(msg)
                    st.info("O treinamento pode levar alguns minutos. Aguarde e depois atualize a página.")
    
    # Exibir previsão de geração
    elif selecao == "Previsão de Geração":
        exibir_previsao_geracao()
    
    # Exibir detecção de anomalias
    elif selecao == "Detecção de Anomalias":
        exibir_deteccao_anomalias()
    
    # Exibir insights
    elif selecao == "Insights":
        st.subheader("Gerar Insights")
        col_periodo = st.columns(2)
        with col_periodo[0]:
            data_inicio = st.date_input("Data início para análise", value=date.today().replace(day=1))
        with col_periodo[1]:
            data_fim = st.date_input("Data fim para análise", value=date.today())
        
        data_inicio_str = data_inicio.isoformat()
        data_fim_str = data_fim.isoformat()
        
        if st.button("Gerar Insights"):
            with st.spinner("Gerando insights..."):
                insights = obter_insights(data_inicio_str, data_fim_str)
                
                # Tentar obter dados do dashboard normal para complementar os insights
                try:
                    resp = requests.get(f"{API_URL}/agregacao/dash")
                    dashboard_data = resp.json() if resp.ok else None
                except:
                    dashboard_data = None
                
                if not exibir_insights(insights, dashboard_data):
                    st.warning("Não foi possível gerar insights para o período selecionado.")
                    status_modelos = obter_status_modelos()
                    if status_modelos.get("status") == "nao_treinado":
                        st.info("Você precisa treinar modelos primeiro para poder gerar insights.") 