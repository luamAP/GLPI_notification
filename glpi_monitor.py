import requests
import os
from dotenv import load_dotenv

import base64

# Carrega as vars do arquivo .env
load_dotenv()

# ==========================================
# CONFIGURAÇÕES
# ==========================================
GLPI_API_URL = os.getenv("GLPI_API_URL")
APP_TOKEN = os.getenv("GLPI_APP_TOKEN")
USER_TOKEN = os.getenv("GLPI_USER_TOKEN")
SENHA_GLPI = os.getenv("SENHA_GLPI")
LOGIN_GLPI = os.getenv("LOGIN_GLPI")

def iniciar_sessao_glpi():
    """
    Tenta autenticar na API do GLPI e retornar o token de sessão.
    """
    # Substitua com sua senha real de acesso ao GLPI
    login_str = f"{LOGIN_GLPI}:{SENHA_GLPI}"
    
    # Converte 'luan.pinto:senha' para Base64 como a documentação exige
    b64_cred = base64.b64encode(login_str.encode('utf-8')).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"user_token {USER_TOKEN}",
        "Authorization": f"Basic {b64_cred}",
        "App-Token": APP_TOKEN
    }
    
    print("Tentando conectar ao GLPI...")
    
    try:
        # Endpoint para iniciar a sessão
        url = f"{GLPI_API_URL}/initSession"
        response = requests.get(url, headers=headers)
        
        # Levanta uma exceção se o status HTTP for um erro (4xx ou 5xx)
        response.raise_for_status() 
        
        session_token = response.json().get("session_token")
        print(f"Sucesso! Sessão iniciada. Token: {session_token[:10]}...")
        return session_token
        
    except requests.exceptions.RequestException as erro:
        print(f"Erro grave de conexão: {erro}")
        if response is not None:
            print(f"Detalhes: {response.text}")
        return None

if __name__ == "__main__":
    sessao = iniciar_sessao_glpi()
    
    if sessao:
        print("Fase 1.1 concluída. Estamos dentro.")
    else:
        print("Falha na Fase 1.1. Revise suas credenciais e URL.")