import streamlit as st
import requests
from datetime import date
import os
import json
import re

API_URL = "http://localhost:8000"

# Caminho absoluto para a pasta de resultados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(BASE_DIR, "backend", "app", "workers", "results_analises")

# Função auxiliar para requisições assíncronas
def requisicao_agregacao(endpoint, payload):
    resp = requests.post(f"{API_URL}/agregacao/{endpoint}", json=payload)
    if resp.status_code == 202:
        return None, resp.json().get("msg", "Processamento assíncrono iniciado.")
    elif resp.ok:
        return resp.json(), None
    else:
        return None, f"Erro: {resp.text}"

def extrai_data_nome_arquivo(nome):
    m = re.search(r'_(\d{8}_\d{6})', nome)
    if m:
        return m.group(1)
    return "00000000_000000"

def render_dashboard():
    st.title("Dashboard - Visão Geral")

    st.header("Indicadores Principais")
    col_periodo = st.columns(2)
    with col_periodo[0]:
        data_inicio = st.date_input("Data início para análise", value=date.today().replace(day=1), key="inicio")
    with col_periodo[1]:
        data_fim = st.date_input("Data fim para análise", value=date.today(), key="fim")
    data_inicio_str = data_inicio.isoformat()
    data_fim_str = data_fim.isoformat()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gerar nova análise do período", key="analisar"):
            # Dispara as três análises principais
            payload_usina = {"data_inicio": data_inicio_str, "data_fim": data_fim_str, "usina_id": 1}
            requisicao_agregacao("geracao_usina", payload_usina)
            payload_pot = {"data_inicio": data_inicio_str, "data_fim": data_fim_str, "inversor_id": 1}
            requisicao_agregacao("potencia_maxima", payload_pot)
            payload_temp = {"data_inicio": data_inicio_str, "data_fim": data_fim_str, "inversor_id": 1}
            requisicao_agregacao("media_temperatura", payload_temp)
            st.success("Solicitações de análise enviadas! Aguarde alguns segundos e clique em 'Atualizar visualização'.")
    with col2:
        if st.button("Atualizar visualização", key="atualizar"):
            st.rerun()

    # Buscar arquivos de análise
    arquivos = []
    if os.path.exists(RESULTS_DIR):
        arquivos = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')]
        arquivos.sort(key=lambda x: extrai_data_nome_arquivo(x), reverse=True)

    if not arquivos:
        st.info("Nenhuma análise encontrada. Clique em 'Gerar nova análise do período' para começar.")
        return

    # Exibir a análise mais recente de cada tipo relevante para o período selecionado
    tipos = ["geracao_usina", "potencia_maxima", "media_temperatura"]
    analises = {tipo: None for tipo in tipos}
    for arq in arquivos:
        for tipo in tipos:
            if arq.startswith(tipo) and analises[tipo] is None:
                caminho = os.path.join(RESULTS_DIR, arq)
                with open(caminho, 'r', encoding='utf-8') as f:
                    dado = json.load(f)
                # Verifica se a análise é do período selecionado
                params = dado.get('parametros', {})
                if params.get('data_inicio') == data_inicio_str and params.get('data_fim') == data_fim_str:
                    analises[tipo] = dado

    st.markdown("---")
    st.subheader(f"Indicadores do Período {data_inicio_str} a {data_fim_str} (mais recente)")
    col1, col2, col3 = st.columns(3)
    with col1:
        if analises["geracao_usina"]:
            st.metric("Geração Total (kWh)", analises["geracao_usina"]["resultado"])
        else:
            st.metric("Geração Total (kWh)", "-")
    with col2:
        if analises["potencia_maxima"]:
            resultado = analises["potencia_maxima"]["resultado"]
            if isinstance(resultado, list) and resultado:
                st.metric("Potência Máxima (W)", resultado[0].get("potencia_maxima", "-"))
            else:
                st.metric("Potência Máxima (W)", "-")
        else:
            st.metric("Potência Máxima (W)", "-")
    with col3:
        if analises["media_temperatura"]:
            resultado = analises["media_temperatura"]["resultado"]
            if isinstance(resultado, list) and resultado:
                st.metric("Temperatura Média (°C)", f'{resultado[0].get("media_temperatura", "-"):.2f}')
            else:
                st.metric("Temperatura Média (°C)", "-")
        else:
            st.metric("Temperatura Média (°C)", "-")

    st.markdown("---")
    st.subheader("Últimas análises geradas")
    for arq in arquivos[:5]:
        caminho = os.path.join(RESULTS_DIR, arq)
        with open(caminho, 'r', encoding='utf-8') as f:
            dado = json.load(f)
        with st.expander(f"{dado['tipo'].replace('_', ' ').title()} - {arq}", expanded=False):
            st.write("**Parâmetros:**")
            for k, v in dado['parametros'].items():
                st.write(f"{k}: {v}")
            st.write("**Resultado:**")
            if isinstance(dado['resultado'], list) and dado['resultado'] and isinstance(dado['resultado'][0], dict):
                st.dataframe(dado['resultado'])
            else:
                st.write(dado['resultado'])

    st.markdown("---")
    st.header("Geração por Usina (Exemplo)")
    # Exemplo de chamada para geração da usina no mês
    payload = {"data_inicio": date.today().replace(day=1).isoformat(), "data_fim": data_fim_str, "usina_id": 1}
    _, msg = requisicao_agregacao("geracao_usina", payload)
    st.info(msg or "Aguardando processamento")

    st.write("Aqui serão exibidos insights, gráficos e agregações principais.")
    # Implementação detalhada será feita por último 