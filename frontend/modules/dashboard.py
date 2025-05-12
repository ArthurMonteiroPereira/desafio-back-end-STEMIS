import streamlit as st
import requests
from datetime import date

API_URL = "http://localhost:8000"

# Função auxiliar para requisições assíncronas
def requisicao_agregacao(endpoint, payload):
    resp = requests.post(f"{API_URL}/agregacao/{endpoint}", json=payload)
    if resp.status_code == 202:
        return None, resp.json().get("msg", "Processamento assíncrono iniciado.")
    elif resp.ok:
        return resp.json(), None
    else:
        return None, f"Erro: {resp.text}"

def render_dashboard():
    st.title("Dashboard - Visão Geral")

    st.header("Indicadores Principais")
    col1, col2, col3 = st.columns(3)
    hoje = date.today().isoformat()

    with col1:
        payload = {"data_inicio": hoje, "data_fim": hoje, "usina_id": 1}
        _, msg = requisicao_agregacao("geracao_usina", payload)
        st.metric("Geração Total Hoje (kWh)", msg or "Aguardando processamento")

    with col2:
        payload = {"data_inicio": hoje, "data_fim": hoje, "inversor_id": 1}
        _, msg = requisicao_agregacao("potencia_maxima", payload)
        st.metric("Potência Máxima Hoje (W)", msg or "Aguardando processamento")

    with col3:
        payload = {"data_inicio": hoje, "data_fim": hoje, "inversor_id": 1}
        _, msg = requisicao_agregacao("media_temperatura", payload)
        st.metric("Temperatura Média Hoje (°C)", msg or "Aguardando processamento")

    st.markdown("---")
    st.header("Geração por Usina (Exemplo)")
    # Exemplo de chamada para geração da usina no mês
    payload = {"data_inicio": date.today().replace(day=1).isoformat(), "data_fim": hoje, "usina_id": 1}
    _, msg = requisicao_agregacao("geracao_usina", payload)
    st.info(msg or "Aguardando processamento")

    st.write("Aqui serão exibidos insights, gráficos e agregações principais.")
    # Implementação detalhada será feita por último 