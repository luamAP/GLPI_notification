import requests
import os
from dotenv import load_dotenv

import base64
import json

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
        if response is not None: print(f"Detalhes: {response.text}")
        return None

def buscar_chamados_recentes(session_token):
    """
    Busca os últimos chamados no GLPI para análise da estrutura de dados.
    """
    headers = {
        "Content-Type": "application/json",
        "Session-Token": session_token
    }
    
    # Se estiver usando App-Token, ele deve ir em todas as requisições subsequentes
    if APP_TOKEN: headers["App-Token"] = APP_TOKEN
        
    print("\nBuscando chamados recentes...")
    
    try:
        url_base_limpa = GLPI_API_URL.rstrip('/')
        # ...
        url = f"{url_base_limpa}/search/Ticket"
        
        # --- ALTERE O DICIONÁRIO PARAMS PARA ESTE AQUI ---
        # Filtro Server-Side: Pedimos apenas chamados Novos (1) OU Atribuídos (2)
        params = {
            "range": "0-10", # Aumentei para 10 para varrer mais possibilidades
            "sort": "1",
            "order": "DESC",
            # Condição 1: Status (campo 12) igual a 1 (Novo)
            "criteria[0][field]": "12",
            "criteria[0][searchtype]": "equals",
            "criteria[0][value]": "1",
            # Condição 2: OU Status (campo 12) igual a 2 (Atribuído)
            "criteria[1][link]": "OR",
            "criteria[1][field]": "12",
            "criteria[1][searchtype]": "equals",
            "criteria[1][value]": "2"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() 
        
        dados = response.json()
        
        # A documentação indica que a resposta tem a chave "data" com a lista de itens
        return dados.get("data", [])
        
    except requests.exceptions.RequestException as erro:
        print(f"Erro ao buscar chamados: {erro}")
        return []

def processar_chamados_brutos(lista_chamados_brutos):
    """
    Recebe a lista bruta do GLPI e extrai apenas os dados estruturados
    necessários para o envio do WhatsApp.
    """
    chamados_limpos = []
    
    for chamado in lista_chamados_brutos:
        # Uso do .get() é uma prática defensiva essencial em integrações
        # Se a chave não existir, retorna None em vez de quebrar o script
        id_chamado = chamado.get('2')
        titulo = chamado.get('1')
        id_tecnico = chamado.get('5')
        status = chamado.get('12')
        
        # Ignora registros que por algum motivo vieram sem ID
        if not id_chamado: continue
            
        chamados_limpos.append({
            "id_chamado": id_chamado,
            "titulo": titulo,
            "id_tecnico": id_tecnico,
            "status": status
        })
        
    return chamados_limpos

def carregar_mapa_tecnicos(caminho_arquivo="tecnicos.json"):
    """
    Carrega o arquivo JSON com o de-para de IDs e telefones dos técnicos.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return {}
    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar o arquivo JSON. Verifique a formatação.")
        return {}

if __name__ == "__main__":
    sessao = iniciar_sessao_glpi()
    
    if not sessao: print("Falha na Fase 1.1.")
    else: 
        print("Fase 1.1 concluída. Estamos dentro.")
        
        chamados = buscar_chamados_recentes(sessao)
        print(chamados)
        
        if chamados:
            chamados_padronizados = processar_chamados_brutos(chamados)
            mapa_tecnicos = carregar_mapa_tecnicos()
            
            print("\n--- INICIANDO CRUZAMENTO DE DADOS ---")
            for chamado in chamados_padronizados:
                # Se o chamado não tem técnico atribuído (None), não há para quem enviar mensagem.
                if chamado['id_tecnico'] is None:
                    print(f"-> [INFO] Chamado {chamado['id_chamado']} ('{chamado['titulo']}') está Novo/Sem técnico. Aguardando triagem.")
                    continue
                    
                id_tec = str(chamado['id_tecnico']) # Garantindo que é string para buscar no JSON
                
                # Ignorando chamados fechados (6) e solucionados (5) - ajuste conforme sua regra de negócios
                if chamado['status'] in [5, 6]:
                    print(f"Chamado {chamado['id_chamado']} ignorado (Status: {chamado['status']} - Encerrado/Solucionado).")
                    continue
                
                # Buscando o técnico no JSON
                tecnico_info = mapa_tecnicos.get(id_tec)
                
                if tecnico_info:
                    print(f"-> [ENVIAR ZAP] Chamado {chamado['id_chamado']} ('{chamado['titulo']}') "
                          f"para {tecnico_info['nome_completo']} no número {tecnico_info['telefone']}.")
                    # Aqui entrará a função da Fase 3 (Evolution API)
                else:
                    print(f"-> [ERRO] Técnico ID {id_tec} não encontrado no JSON. Chamado {chamado['id_chamado']} retido.")
                    
        else:
            print("\nNenhum chamado retornado.")
        
