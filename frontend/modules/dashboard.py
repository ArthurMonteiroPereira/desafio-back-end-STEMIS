import streamlit as st
import requests
from datetime import date, datetime
import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import time

API_URL = "http://localhost:8000"

# Caminho absoluto para a pasta de resultados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(BASE_DIR, "backend", "app", "workers", "results_analises")

# Função para obter todas as usinas da API
def obter_usinas():
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

# Função para obter todos os inversores da API
def obter_inversores():
    try:
        resp = requests.get(f"{API_URL}/inversores/")
        if resp.ok:
            return resp.json()
        else:
            st.error(f"Erro ao obter inversores: {resp.text}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

# Função para obter inversores por usina
def obter_inversores_por_usina(usina_id):
    """
    Retorna todos os inversores associados a uma usina específica consultando a API.
    """
    try:
        inversores = obter_inversores()
        if not inversores:
            st.warning(f"Não foi possível obter inversores da API. Usando valores padrão para usina {usina_id}.")
            if usina_id == 1:
                return [{"id": i} for i in range(1, 5)]
            elif usina_id == 2:
                return [{"id": i} for i in range(5, 9)]
            return []
        
        # Filtrar inversores pela usina_id
        inversores_da_usina = [inv for inv in inversores if inv.get("usina_id") == usina_id]
        
        if not inversores_da_usina:
            st.warning(f"Nenhum inversor encontrado para a usina {usina_id}.")
        
        return inversores_da_usina
    except Exception as e:
        st.error(f"Erro ao obter inversores por usina: {str(e)}")
        return []

# Função auxiliar para requisições assíncronas
def requisicao_agregacao(endpoint, payload):
    resp = requests.post(f"{API_URL}/agregacao/{endpoint}", json=payload)
    if resp.status_code == 202:
        return None, resp.json().get("msg", "Processamento assíncrono iniciado.")
    elif resp.ok:
        return resp.json(), None
    else:
        return None, f"Erro: {resp.text}"

# Função para obter resultados de análises da API
def obter_resultados_analises(tipo=None, usina_id=None, inversor_id=None):
    """
    Obtém resultados de análises da API com filtros opcionais.
    """
    params = {}
    if tipo:
        params['tipo'] = tipo
    if usina_id:
        params['usina_id'] = usina_id
    if inversor_id:
        params['inversor_id'] = inversor_id
    
    try:
        resp = requests.get(f"{API_URL}/agregacao/resultados", params=params)
        if resp.ok:
            return resp.json()
        else:
            st.error(f"Erro ao obter resultados: {resp.text}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

# Função para obter uma análise específica pelo nome do arquivo
def obter_resultado_analise(nome_arquivo):
    """
    Obtém um resultado específico de análise pelo nome do arquivo.
    """
    try:
        resp = requests.get(f"{API_URL}/agregacao/resultado/{nome_arquivo}")
        if resp.ok:
            return resp.json()
        else:
            st.error(f"Erro ao obter resultado: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

# Função para obter a análise mais recente de um determinado tipo
def obter_analise_mais_recente(tipo, parametro_adicional=None):
    """
    Obtém a análise mais recente de um determinado tipo.
    
    :param tipo: Tipo de análise (ex: geracao_usina)
    :param parametro_adicional: Dicionário com parâmetros adicionais para filtrar (ex: {"usina_id": 1})
    :return: Dados da análise mais recente ou None se não encontrar
    """
    try:
        params = {}
        if tipo:
            params['tipo'] = tipo
        
        if parametro_adicional:
            for chave, valor in parametro_adicional.items():
                params[chave] = valor
        
        resultados = obter_resultados_analises(**params)
        
        if resultados and len(resultados) > 0:
            # O primeiro resultado já é o mais recente
            nome_arquivo = resultados[0]["nome_arquivo"]
            return obter_resultado_analise(nome_arquivo)
        
        return None
    except Exception as e:
        st.error(f"Erro ao obter análise mais recente: {str(e)}")
        return None

def exibir_mensagem_sem_dados(usina_id=None, data_inicio_str=None, data_fim_str=None):
    """
    Exibe uma mensagem informativa quando não há dados disponíveis.
    """
    if not data_inicio_str or not data_fim_str:
        st.info("Período de análise não definido. Por favor, selecione as datas de início e fim.")
        return
    
    if usina_id and usina_id > 0:
        st.info(f"Nenhum dado encontrado para a Usina {usina_id} no período de {data_inicio_str} a {data_fim_str}. Clique em 'Atualizar dados da Usina {usina_id}' para gerar.")
    else:
        st.info(f"Nenhum dado encontrado para o período de {data_inicio_str} a {data_fim_str}. Clique em 'Gerar nova análise do período' para começar.")

# Função para gerar dashboard
def gerar_dashboard(data_inicio, data_fim):
    """
    Solicita a geração do dashboard para o período especificado.
    """
    try:
        payload = {
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
        resp = requests.post(f"{API_URL}/agregacao/gerar_dash", json=payload)
        if resp.ok:
            return resp.json().get("msg", "Solicitação de geração do dashboard enviada.")
        else:
            return f"Erro: {resp.text}"
    except Exception as e:
        return f"Erro de conexão: {str(e)}"

# Função para obter dados do dashboard
def obter_dashboard():
    """
    Obtém os dados mais recentes do dashboard.
    """
    try:
        resp = requests.get(f"{API_URL}/agregacao/dash")
        if resp.ok:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            st.error(f"Erro ao obter dados do dashboard: {resp.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def exibir_grafico_geracao(dados_serie_temporal, titulo, dias_no_eixo=7):
    """
    Exibe um gráfico de geração com base nos dados de série temporal.
    Limita o número de datas no eixo X para melhor visualização.
    """
    try:
        if not dados_serie_temporal:
            st.info("Não há dados suficientes para gerar o gráfico.")
            return

        # Criar dataframe
        df = pd.DataFrame(dados_serie_temporal)
        
        # Converter dia para datetime
        df['dia'] = pd.to_datetime(df['dia'])
        df = df.sort_values('dia')
        
        # Configurar o índice
        df_plot = df.set_index('dia')
        
        # Exibir o gráfico
        st.subheader(titulo)
        st.line_chart(df_plot['geracao'])
        
        # Exibir estatísticas
        if not df.empty:
            # Dias com geração > 0
            df_com_geracao = df[df['geracao'] > 0]
            total_dias_com_geracao = len(df_com_geracao)
            
            if total_dias_com_geracao > 0:
                geracao_total = df['geracao'].sum()
                media_diaria = geracao_total / total_dias_com_geracao
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Geração total (kWh)", f"{geracao_total:.2f}")
                with col2:
                    st.metric("Média diária (kWh/dia)", f"{media_diaria:.2f}")
                with col3:
                    st.metric("Dias com geração", f"{total_dias_com_geracao}")
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

def render_dashboard():
    st.title("Dashboard - Visão Geral")

    st.header("Indicadores Principais")
    col_periodo = st.columns(2)
    with col_periodo[0]:
        data_inicio = st.date_input("Data início para análise", value=date.today().replace(day=1))
    with col_periodo[1]:
        data_fim = st.date_input("Data fim para análise", value=date.today())
    data_inicio_str = data_inicio.isoformat()
    data_fim_str = data_fim.isoformat()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gerar nova análise do período", key="analisar"):
            with st.spinner("Solicitando análise do período..."):
                msg = gerar_dashboard(data_inicio_str, data_fim_str)
                st.success(msg)
                st.info("Aguarde alguns segundos e clique em 'Atualizar visualização' para ver os resultados.")
    with col2:
        if st.button("Atualizar visualização", key="atualizar"):
            st.rerun()

    # Tentar obter dados do dashboard
    dashboard_data = obter_dashboard()

    if not dashboard_data:
        st.warning("Nenhum dashboard encontrado. Clique em 'Gerar nova análise do período' para começar.")
        return

    # Extrair período do dashboard
    periodo = dashboard_data.get("periodo", {})
    periodo_str = f"{periodo.get('data_inicio', '')} a {periodo.get('data_fim', '')}"
    
    # Exibir timestamp da geração
    st.caption(f"Dashboard gerado em: {dashboard_data.get('geracao_timestamp', '')}")
    
    # Exibir indicadores globais
    st.markdown("---")
    st.subheader(f"Indicadores Globais - Período: {periodo_str}")
    
    metricas_globais = dashboard_data.get("metricas_globais", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Geração Total (kWh)", f"{metricas_globais.get('geracao_total', 0):.2f}")
    with col2:
        st.metric("Potência Máxima Total (W)", f"{metricas_globais.get('potencia_maxima_total', 0):.2f}")
    with col3:
        temp_media = metricas_globais.get("temperatura_media_global", 0)
        st.metric("Temperatura Média (°C)", f"{temp_media:.2f}" if temp_media else "-")
    
    # Exibir médias diárias
    st.markdown("### Médias Diárias")
    col1, col2 = st.columns(2)
    with col1:
        media_diaria = metricas_globais.get("media_diaria_geracao", 0)
        st.metric("Média Diária de Geração (kWh/dia)", f"{media_diaria:.2f}")
    with col2:
        media_potencia = metricas_globais.get("media_diaria_potencia", 0)
        st.metric("Média Diária de Potência (W)", f"{media_potencia:.2f}")
    
    # Exibir gráfico global
    serie_temporal_total = dashboard_data.get("serie_temporal_total", [])
    if serie_temporal_total:
        # Exibir gráfico com guias
        st.markdown("### Histórico Global")
        tab1, tab2, tab3 = st.tabs(["Geração (kWh)", "Potência Máxima (W)", "Temperatura Média (°C)"])
        
        with tab1:
            # Criar dataframe para geração
            df_geracao = pd.DataFrame([
                {"dia": item["dia"], "valor": item["geracao"]} 
                for item in serie_temporal_total
            ])
            if not df_geracao.empty:
                df_geracao['dia'] = pd.to_datetime(df_geracao['dia'])
                df_geracao = df_geracao.sort_values('dia').set_index('dia')
                st.line_chart(df_geracao)
        
        with tab2:
            # Criar dataframe para potência
            df_potencia = pd.DataFrame([
                {"dia": item["dia"], "valor": item["potencia_maxima"]} 
                for item in serie_temporal_total
            ])
            if not df_potencia.empty:
                df_potencia['dia'] = pd.to_datetime(df_potencia['dia'])
                df_potencia = df_potencia.sort_values('dia').set_index('dia')
                st.line_chart(df_potencia)
                
        with tab3:
            # Criar dataframe para temperatura
            df_temp = pd.DataFrame([
                {"dia": item["dia"], "valor": item["temperatura_media"]} 
                for item in serie_temporal_total
            ])
            if not df_temp.empty:
                df_temp['dia'] = pd.to_datetime(df_temp['dia'])
                df_temp = df_temp.sort_values('dia').set_index('dia')
                st.line_chart(df_temp)
    
    # Exibir seleção de usina
    st.markdown("---")
    st.header("Análise por Usina")
    
    # Obter lista de usinas do dashboard
    usinas = dashboard_data.get("usinas", [])
    
    if not usinas:
        st.warning("Nenhuma usina encontrada no dashboard.")
        return
    
    # Opções do dropdown
    opcoes_usina = [{"id": 0, "nome": "Todas as Usinas"}] + usinas
    opcoes_mapeadas = {usina["nome"]: usina["id"] for usina in opcoes_usina}
    
    # Dropdown para selecionar usina
    usina_selecionada = st.selectbox(
        "Selecione a Usina", 
        options=list(opcoes_mapeadas.keys())
    )
    
    usina_id = opcoes_mapeadas[usina_selecionada]
    
    # Se "Todas as Usinas" estiver selecionado, mostrar comparativo entre usinas
    if usina_id == 0:
        st.subheader("Comparativo entre Usinas")
        
        # Criar dataframe para o comparativo
        dados_usinas = []
        for usina in usinas:
            dados_usinas.append({
                "nome": usina["nome"],
                "geracao_total": usina["metricas"]["geracao_total"],
                "potencia_maxima": usina["metricas"]["potencia_maxima_total"],
                "temperatura_media": usina["metricas"]["temperatura_media"]
            })
        
        if dados_usinas:
            df_usinas = pd.DataFrame(dados_usinas)
            
            # Exibir tabela comparativa
            st.dataframe(df_usinas.set_index("nome"))
            
            # Gráfico de barras para geração
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(df_usinas["nome"], df_usinas["geracao_total"])
            ax.set_title('Geração Total por Usina (kWh)')
            ax.set_xlabel('Usina')
            ax.set_ylabel('Geração (kWh)')
            
            # Adicionar valores sobre as barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{height:.2f}', ha='center', va='bottom')
            
            st.pyplot(fig)
            
            # Gráfico de série temporal comparando usinas
            st.subheader("Geração Diária por Usina")
            
            # Criar dataframe para comparação temporal
            dados_temporais = []
            for item in serie_temporal_total:
                dia = item["dia"]
                for usina_id_str, usina_dados in item.get("usinas", {}).items():
                    dados_temporais.append({
                        "dia": dia,
                        "usina": usina_dados.get("nome", f"Usina {usina_id_str}"),
                        "geracao": usina_dados.get("geracao", 0)
                    })
            
            if dados_temporais:
                # Criar dataframe
                df_temporal = pd.DataFrame(dados_temporais)
                df_temporal['dia'] = pd.to_datetime(df_temporal['dia'])
                
                # Criar pivot para gráfico
                df_pivot = df_temporal.pivot(index='dia', columns='usina', values='geracao')
                
                # Exibir gráfico
                st.line_chart(df_pivot)
    else:
        # Exibir dados da usina selecionada
        usina_dados = next((u for u in usinas if u["id"] == usina_id), None)
        
        if not usina_dados:
            st.warning(f"Dados da Usina {usina_id} não encontrados.")
            return
            
        st.subheader(f"Dados da {usina_dados['nome']}")
        
        # Exibir métricas da usina
        metricas_usina = usina_dados.get("metricas", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Geração Total (kWh)", f"{metricas_usina.get('geracao_total', 0):.2f}")
        with col2:
            st.metric("Potência Máxima (W)", f"{metricas_usina.get('potencia_maxima_total', 0):.2f}")
        with col3:
            st.metric("Temperatura Média (°C)", f"{metricas_usina.get('temperatura_media', 0):.2f}")
    
        # Exibir médias diárias
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Média Diária (kWh/dia)", f"{metricas_usina.get('media_diaria_geracao', 0):.2f}")
        with col2:
            # Calcular dias com geração
            serie_temporal_usina = dashboard_data.get("serie_temporal_usinas", {}).get(str(usina_id), [])
            dias_com_geracao = len([d for d in serie_temporal_usina if d.get("geracao", 0) > 0])
            st.metric("Dias com Geração", f"{dias_com_geracao}")
            
        # Exibir gráfico da usina
        if serie_temporal_usina:
            # Criar dataframe
            df_usina = pd.DataFrame(serie_temporal_usina)
            
            if not df_usina.empty:
                # Converter dia para datetime
                df_usina['dia'] = pd.to_datetime(df_usina['dia'])
                df_usina = df_usina.sort_values('dia')
                
                # Exibir gráfico com guias
                st.markdown("### Histórico da Usina")
                tab1, tab2, tab3 = st.tabs(["Geração (kWh)", "Potência Máxima (W)", "Temperatura Média (°C)"])
                
                with tab1:
                    st.line_chart(df_usina.set_index('dia')['geracao'])
                
                with tab2:
                    st.line_chart(df_usina.set_index('dia')['potencia_maxima'])
                    
                with tab3:
                    st.line_chart(df_usina.set_index('dia')['temperatura_media'])
                
                # Exibir estatísticas
                df_com_geracao = df_usina[df_usina['geracao'] > 0]
                if not df_com_geracao.empty:
                    total_geracao = df_usina['geracao'].sum()
                    media_diaria = total_geracao / len(df_com_geracao)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Geração Total no Período (kWh)", f"{total_geracao:.2f}")
                    with col2:
                        st.metric("Média Diária de Geração (kWh/dia)", f"{media_diaria:.2f}")
        
        # Exibir dados dos inversores
        inversores = usina_dados.get("inversores", [])
        if inversores:
            st.subheader(f"Inversores da {usina_dados['nome']}")
            st.write(f"Total de {len(inversores)} inversores")
            
            # Criar dataframe para o comparativo
            dados_inversores = []
            for inversor in inversores:
                metricas_inv = inversor.get("metricas", {})
                dados_inversores.append({
                    "ID": inversor["id"],
                    "Nome": inversor.get("nome", f"Inversor {inversor['id']}"),
                    "Geração (kWh)": metricas_inv.get("geracao_total", 0),
                    "Potência Máxima (W)": metricas_inv.get("potencia_maxima", 0),
                    "Temperatura Média (°C)": metricas_inv.get("temperatura_media", 0)
                })
            
            # Exibir tabela comparativa
            st.dataframe(pd.DataFrame(dados_inversores))
            
            # Gráfico de barras para geração dos inversores
            if dados_inversores:
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar([inv["Nome"] for inv in dados_inversores], 
                              [inv["Geração (kWh)"] for inv in dados_inversores])
                ax.set_title('Geração por Inversor (kWh)')
                ax.set_xlabel('Inversor')
                ax.set_ylabel('Geração (kWh)')
                
                # Adicionar valores sobre as barras
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{height:.2f}', ha='center', va='bottom')
                
                st.pyplot(fig) 