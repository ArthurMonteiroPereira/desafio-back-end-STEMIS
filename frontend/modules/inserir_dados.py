import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

def render_inserir_dados():
    st.title("Inserir Dados Manualmente")

    # Buscar usinas e inversores logo no início
    try:
        usinas = requests.get(f"{API_URL}/usinas/").json()
        usina_options = {f"{u['nome']} (ID {u['id']})": u['id'] for u in usinas}
    except:
        usina_options = {}

    try:
        inversores = requests.get(f"{API_URL}/inversores/").json()
        inversor_options = {f"{i['nome']} (ID {i['id']})": i['id'] for i in inversores}
    except:
        inversor_options = {}

    st.subheader("Cadastrar Usina")
    with st.form("form_usina"):
        nome_usina = st.text_input("Nome da Usina")
        localizacao_usina = st.text_input("Localização")
        submitted_usina = st.form_submit_button("Cadastrar Usina")
        if submitted_usina and nome_usina:
            payload = {"nome": nome_usina, "localizacao": localizacao_usina}
            try:
                resp = requests.post(f"{API_URL}/usinas/", json=payload)
                if resp.status_code == 201:
                    st.success("Usina cadastrada com sucesso!")
                else:
                    st.error(f"Erro: {resp.text}")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")

    st.markdown("---")
    st.subheader("Cadastrar Inversor")
    with st.form("form_inversor"):
        nome_inv = st.text_input("Nome do Inversor")
        modelo_inv = st.text_input("Modelo do Inversor")
        usina_id_inv = st.selectbox("Usina", options=list(usina_options.keys())) if usina_options else None
        submitted_inv = st.form_submit_button("Cadastrar Inversor")
        if submitted_inv and nome_inv and usina_id_inv:
            payload = {
                "nome": nome_inv,
                "modelo": modelo_inv,
                "usina_id": usina_options[usina_id_inv]
            }
            try:
                resp = requests.post(f"{API_URL}/inversores/", json=payload)
                if resp.status_code == 201:
                    st.success("Inversor cadastrado com sucesso!")
                else:
                    st.error(f"Erro: {resp.text}")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")

    st.markdown("---")
    st.subheader("Cadastrar Medição")
    with st.form("form_medicao"):
        inversor_id = st.selectbox("Inversor", options=list(inversor_options.keys())) if inversor_options else None
        data = st.date_input("Data da Medição", value=datetime.now().date())
        hora = st.time_input("Hora da Medição", value=datetime.now().time())
        timestamp = datetime.combine(data, hora)
        potencia_ativa = st.number_input("Potência Ativa (W)", min_value=0.0, step=0.1)
        temperatura = st.number_input("Temperatura (°C)", step=0.1)
        submitted_med = st.form_submit_button("Cadastrar Medição")
        if submitted_med and inversor_id:
            payload = {
                "inversor_id": inversor_options[inversor_id],
                "timestamp": timestamp.isoformat(),
                "potencia_ativa": potencia_ativa,
                "temperatura": temperatura
            }
            try:
                resp = requests.post(f"{API_URL}/medicoes/", json=payload)
                if resp.status_code == 201:
                    st.success("Medição cadastrada com sucesso!")
                else:
                    st.error(f"Erro: {resp.text}")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}")
