import streamlit as st
import requests
from datetime import datetime, date

API_URL = "http://localhost:8000"

def render_consultar_dados():
    st.title("Consultar Dados")

    st.header("Usinas")
    try:
        usinas = requests.get(f"{API_URL}/usinas/").json()
        if usinas:
            colunas_usina = list(usinas[0].keys())
            coluna_filtro_usina = st.selectbox("Coluna para filtrar (Usinas)", colunas_usina)
            valor_filtro_usina = st.text_input("Valor para filtrar (Usinas)")
            if valor_filtro_usina:
                usinas = [u for u in usinas if valor_filtro_usina.lower() in str(u[coluna_filtro_usina]).lower()]
            st.dataframe(usinas)
        else:
            st.info("Nenhuma usina cadastrada.")
    except Exception as e:
        st.error(f"Erro ao buscar usinas: {e}")

    st.markdown("---")
    st.header("Inversores")
    try:
        inversores = requests.get(f"{API_URL}/inversores/").json()
        if inversores:
            colunas_inv = list(inversores[0].keys())
            coluna_filtro_inv = st.selectbox("Coluna para filtrar (Inversores)", colunas_inv)
            valor_filtro_inv = st.text_input("Valor para filtrar (Inversores)")
            if valor_filtro_inv:
                inversores = [i for i in inversores if valor_filtro_inv.lower() in str(i[coluna_filtro_inv]).lower()]
            st.dataframe(inversores)
        else:
            st.info("Nenhum inversor cadastrado.")
    except Exception as e:
        st.error(f"Erro ao buscar inversores: {e}")

    st.markdown("---")
    st.header("Medições")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data início", value=date.today().replace(day=1))
    with col2:
        data_fim = st.date_input("Data fim", value=date.today())
    try:
        params = {"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()}
        medicoes = requests.get(f"{API_URL}/medicoes/", params=params).json()
        if medicoes:
            colunas_med = list(medicoes[0].keys())
            coluna_filtro_med = st.selectbox("Coluna para filtrar (Medições)", colunas_med)
            valor_filtro_med = st.text_input("Valor para filtrar (Medições)")
            if valor_filtro_med:
                medicoes = [m for m in medicoes if valor_filtro_med.lower() in str(m[coluna_filtro_med]).lower()]
            st.dataframe(medicoes)
        else:
            st.info("Nenhuma medição encontrada no período.")
    except Exception as e:
        st.error(f"Erro ao buscar medições: {e}") 