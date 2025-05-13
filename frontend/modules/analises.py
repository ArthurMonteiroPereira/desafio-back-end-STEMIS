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

def requisicao_agregacao(endpoint, payload):
    resp = requests.post(f"{API_URL}/agregacao/{endpoint}", json=payload)
    if resp.status_code == 202:
        return None, resp.json().get("msg", "Processamento assíncrono iniciado.")
    elif resp.ok:
        return resp.json(), None
    else:
        return None, f"Erro: {resp.text}"

def extrai_data_nome_arquivo(nome):
    # Espera formato: tipo_YYYYMMDD_HHMMSS.json
    m = re.search(r'_(\d{8}_\d{6})', nome)
    if m:
        return m.group(1)
    return "00000000_000000"

def render_analises():
    st.title("Análises Detalhadas")

    tipo_analise = st.selectbox("Tipo de análise", [
        "Potência máxima por dia",
        "Média da temperatura por dia",
        "Geração da usina por período",
        "Geração do inversor por período"
    ])

    data_inicio = st.date_input("Data início", value=date.today().replace(day=1))
    data_fim = st.date_input("Data fim", value=date.today())

    if tipo_analise == "Potência máxima por dia":
        inversor_id = st.number_input("ID do Inversor", min_value=1, step=1)
        if st.button("Consultar", key="pot_max"):
            payload = {
                "inversor_id": int(inversor_id),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat()
            }
            _, msg = requisicao_agregacao("potencia_maxima", payload)
            st.info(msg or "Aguardando processamento")

    elif tipo_analise == "Média da temperatura por dia":
        inversor_id = st.number_input("ID do Inversor", min_value=1, step=1, key="inv_temp")
        if st.button("Consultar", key="med_temp"):
            payload = {
                "inversor_id": int(inversor_id),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat()
            }
            _, msg = requisicao_agregacao("media_temperatura", payload)
            st.info(msg or "Aguardando processamento")

    elif tipo_analise == "Geração da usina por período":
        usina_id = st.number_input("ID da Usina", min_value=1, step=1, key="usina_ger")
        if st.button("Consultar", key="ger_usina"):
            payload = {
                "usina_id": int(usina_id),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat()
            }
            _, msg = requisicao_agregacao("geracao_usina", payload)
            st.info(msg or "Aguardando processamento")

    elif tipo_analise == "Geração do inversor por período":
        inversor_id = st.number_input("ID do Inversor", min_value=1, step=1, key="inv_ger")
        if st.button("Consultar", key="ger_inv"):
            payload = {
                "inversor_id": int(inversor_id),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat()
            }
            _, msg = requisicao_agregacao("geracao_inversor", payload)
            st.info(msg or "Aguardando processamento")

    st.markdown("---")
    st.header("Resultados das Análises")
    if st.button("Atualizar análises"):
        if os.path.exists(RESULTS_DIR):
            arquivos = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')]
            # Ordenar por data extraída do nome do arquivo, mais recente primeiro
            arquivos.sort(key=lambda x: extrai_data_nome_arquivo(x), reverse=True)
            for arq in arquivos:
                try:
                    caminho = os.path.join(RESULTS_DIR, arq)
                    with open(caminho, 'r', encoding='utf-8') as f:
                        dado = json.load(f)
                    
                    # Verificar se o arquivo possui a chave 'tipo'
                    if 'tipo' not in dado:
                        continue  # Ignorar este arquivo e seguir para o próximo
                        
                    with st.expander(f"{dado['tipo'].replace('_', ' ').title()} - {arq}", expanded=False):
                        st.write("**Parâmetros:**")
                        for k, v in dado['parametros'].items():
                            st.write(f"{k}: {v}")
                        st.write("**Resultado:**")
                        if isinstance(dado['resultado'], list) and dado['resultado'] and isinstance(dado['resultado'][0], dict):
                            st.dataframe(dado['resultado'])
                        else:
                            st.write(dado['resultado'])
                except Exception as e:
                    # Ignorar silenciosamente quaisquer erros e continuar
                    continue
        else:
            st.info("Nenhuma análise encontrada.")


    # Aqui você pode criar forms para POST nos endpoints de agregação e exibir resultados 