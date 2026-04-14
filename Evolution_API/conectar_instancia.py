import os
import requests
from dotenv import load_dotenv
import time
import webbrowser

load_dotenv()

EVOLUTION_API_URL = "http://localhost:8080"
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API")
NOME_INSTANCIA = "suporte_glpi"

def obter_qr_code():
    # Rota GET para conectar/obter o QR code de uma instância existente
    url = f"{EVOLUTION_API_URL}/instance/connect/{NOME_INSTANCIA}"
    
    headers = {
        "apikey": EVOLUTION_API_KEY
    }
    
    print("Buscando o QR Code no servidor...")
    
    for tentativa in range(1, 16): 
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                dados = response.json()
                base64_img = dados.get("base64")
                
                if base64_img:
                    print("\nSUCESSO! Gerando página HTML e abrindo o navegador...")
                    
                    # 1. Monta uma página HTML simples com a imagem
                    html_content = f"""
                    <html>
                    <head><title>QR Code WhatsApp</title></head>
                    <body style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #2e2e2e; color: white; font-family: sans-serif;">
                        <div style="text-align: center;">
                            <h2>Escaneie o QR Code</h2>
                            <p>Válido por 40 segundos.</p>
                            <img src="{base64_img}" alt="QR Code" style="border: 4px solid #075e54; border-radius: 10px; padding: 15px; background: white;" />
                        </div>
                    </body>
                    </html>
                    """
                    
                    # 2. Salva o arquivo na mesma pasta do script
                    caminho_arquivo = os.path.abspath("qrcode_temp.html")
                    with open(caminho_arquivo, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    # 3. Pede para o sistema operacional abrir o arquivo no Chrome/Edge
                    webbrowser.open(f"file://{caminho_arquivo}")
                    
                    print("Página aberta! Escaneie pelo seu celular rapidamente.")
                    return
                    
        except requests.exceptions.RequestException:
            pass # Ignora erros de conexão durante o polling
            
        print(f"[{tentativa}/15] Motor iniciando... Aguardando QR Code...")
        time.sleep(3) 
        
    print("\nFalha: O tempo limite de inicialização foi atingido.")

if __name__ == "__main__":
    obter_qr_code()