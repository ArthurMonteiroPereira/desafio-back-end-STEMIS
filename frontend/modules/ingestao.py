import streamlit as st
import requests

API_URL = "http://localhost:8000"

def render_arquivo():
    st.title("Ingestão de Arquivo")
    st.header("Upload de arquivo para ingestão assíncrona")
    with st.form("upload_form"):
        uploaded_file = st.file_uploader("Selecione um arquivo JSON de medições", type=["json"])
        submitted = st.form_submit_button("Enviar para ingestão")
        if submitted and uploaded_file:
            try:
                response = requests.post(f"{API_URL}/ingestao/arquivo", files={"file": uploaded_file})
                if response.status_code == 202:
                    st.success("Arquivo enviado para processamento assíncrono!")
                else:
                    st.error(f"Erro: {response.text}")
            except Exception as e:
                st.error(f"Erro ao conectar com a API: {e}") 