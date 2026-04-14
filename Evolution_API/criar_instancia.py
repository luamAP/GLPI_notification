import os
import requests
from dotenv import load_dotenv

from conectar_instancia import obter_qr_code

load_dotenv()

EVOLUTION_API_URL = "http://localhost:8080" # Nossa API local no Docker
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API")
NOME_INSTANCIA = "suporte_glpi" # Nome interno da sessão

def criar_e_conectar_instancia():
    url = f"{EVOLUTION_API_URL}/instance/create"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    # Payload de configuração da Evolution API v2
    payload = {
        "instanceName": NOME_INSTANCIA,
        "qrcode": True, # Pede para retornar o QR Code no terminal/base64
        "integration": "WHATSAPP-BAILEYS"
    }
    
    print("Solicitando criação da instância...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        if response.status_code in [200, 201]:
            print("Sucesso! Instância criada no backend.")
        else:
            print(f"Aviso: A API retornou status {response.status_code}. A instância pode já estar criada.")

        obter_qr_code()

    except requests.exceptions.RequestException as e:
        print(f"Erro grave de conexão: {e}")

if __name__ == "__main__":
    criar_e_conectar_instancia()