import os
import requests
import time
import socket
import socketserver
import http.server as server
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL") # API local no Docker
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API")
NOME_INSTANCIA = "suporte_glpi" # Nome interno da sessão

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
                    print("\nSUCESSO! Gerando página HTML...")
                    
                    # 1. Monta uma página HTML simples com a imagem
                    html_content = f"""
                    <html>
                    <head><title>QR Code WhatsApp</title></head>
                    <body style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #2e2e2e; color: white; font-family: sans-serif;">
                        <div style="text-align: center;">
                            <h2>Escaneie o QR Code</h2>
                            <p>Válido por 30 segundos. Atualize a página se expirar.</p>
                            <img src="{base64_img}" alt="QR Code" style="border: 4px solid #075e54; border-radius: 10px; padding: 15px; background: white;" />
                        </div>
                    </body>
                    </html>
                    """
                    
                    # 2. Salva o arquivo na mesma pasta do script
                    caminho_arquivo = os.path.abspath("qrcode_temp.html")
                    with open(caminho_arquivo, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        s.connect(('10.255.255.255', 1))
                        ip_local = s.getsockname()[0]
                    except Exception: ip_local = '127.0.0.1'
                    finally: s.close()

                    PORTA = 8000
                    print(f'''
= = = = = = = = = = = = = = = =  = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
                    📡 SERVIDOR WEB INICIADO NA REDE INTERNA!
                    ➡️ Peça para o dono do celular acessar este link no navegador dele:
                    http://{ip_local}:{PORTA}/qrcode_temp.html

                    ⏳ Pressione CTRL+C neste terminal APÓS o celular ler o QR Code para desligar este servidor.
= = = = = = = = = = = = = = = =  = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
                        ''')
                    
                    # Sobe um servidor web básico na pasta atual para servir o HTML
                    Handler = server.SimpleHTTPRequestHandler
                    # Evita o erro de "Address already in use" caso o script rode duas vezes rápido
                    socketserver.TCPServer.allow_reuse_address = True

                    with socketserver.TCPServer(('', PORTA), Handler) as httpd:
                        try: httpd.serve_forever()
                        except KeyboardInterrupt:
                            print('\nServidor web encerrado. Instância pronta para uso!')
                    
                    return
                    
        except requests.exceptions.RequestException:
            pass # Ignora erros de conexão durante o polling
            
        print(f"[{tentativa}/15] Motor iniciando... Aguardando QR Code...")
        time.sleep(3) 
        
    print("\nFalha: O tempo limite de inicialização foi atingido.")

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
        print(f"[ERRO] grave de conexão: {e}")

def enviar_mensagem_whatsapp(numero, mensagem):
    """
    Limpa o número de telefone e envia uma mensagem de texto pela Evolution API.
    """
    url = f'{EVOLUTION_API_URL}/message/sendText/{NOME_INSTANCIA}'

    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }

    # Tratamento de dados
    numero = ''.join(filter(str.isdigit, str(numero)))

    payload = {
        'number': numero,
        'text': mensagem
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() # Verifica se a API retornou erro (400, 500, etc)
        return True
    except requests.exceptions.RequestException as e:
        print(f'Erro na Evolution API ao enviar mensagem: {e}')
        return False

if __name__ == "__main__":
    criar_e_conectar_instancia()