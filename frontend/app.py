import streamlit as st
from modules.ingestao import render_arquivo
from modules.inserir_dados import render_inserir_dados
from modules.consultar_dados import render_consultar_dados
from modules.analises import render_analises
from modules.dashboard import render_dashboard

st.set_page_config(page_title="Monitoramento de Usinas Fotovoltaicas", layout="wide")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Ir para:",
    [
        "Dashboard",
        "Ingestão de Arquivo",
        "Inserir Dados",
        "Consultar Dados",
        "Análises"
    ]
)

if pagina == "Dashboard":
    render_dashboard()
elif pagina == "Ingestão de Arquivo":
    render_arquivo()
elif pagina == "Inserir Dados":
    render_inserir_dados()
elif pagina == "Consultar Dados":
    render_consultar_dados()
elif pagina == "Análises":
    render_analises() 