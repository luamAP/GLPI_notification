import requests
import os
from dotenv import load_dotenv
import logging

import base64

from Manager_db.db_manager import registrar_notificacao, deletar_chamado
from Evolution_API.criar_instancia import enviar_mensagem_whatsapp

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
ARQUIVO_SESSAO = 'glpi_session.txt'

def obter_token_cache():
    """ Lê o arquivo 'glpi_session.txt' para obter o token """
    try: 
        with open (ARQUIVO_SESSAO, 'r') as f: return f.read().strip()
    except FileNotFoundError: return None
    
def salvar_token_cache(token):
    """ Cria o arquivo 'glpi_session.txt' com o token da API """
    with open(ARQUIVO_SESSAO, 'w') as f:
        f.write(token)

def remove_file(caminho):
    """ Remove o arquivo especificado """
    if os.path.exists(caminho): os.remove(caminho)
    else: logging.error("## Arquivo não existe! ##")

def check_api():
    """ Checa a "Saúde da API" do GLPI """
    login_str = f"{LOGIN_GLPI}:{SENHA_GLPI}"
    b64_cred = base64.b64encode(login_str.encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Session-Token': obter_token_cache(),
        'App-Token': APP_TOKEN
    }

    try:
        url = f'{GLPI_API_URL}/getFullSession'
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
            if e.response.status_code in (401, 403):
                logging.error('Sessão em cache expirou ou é inválida, Renovando...')
                iniciar_sessao_glpi()

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
    
    try:
        # Endpoint para iniciar a sessão
        url = f"{GLPI_API_URL}/initSession"
        response = requests.get(url, headers=headers)
        
        # Levanta uma exceção se o status HTTP for um erro (4xx ou 5xx)
        response.raise_for_status() 
        
        session_token = response.json().get("session_token")
        logging.info(f"Sucesso! Sessão iniciada. Novo Token: {session_token[:10]}")
        salvar_token_cache(session_token)
        
    except requests.exceptions.RequestException as erro:
        logging.error(f"ERRO grave de conexão: {erro}")
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
        logging.error(f"--- ERRO ao buscar chamados: {erro}")
        raise

def processar_chamados_brutos(lista_chamados_brutos):
    """
    Recebe a lista bruta do GLPI e extrai apenas os dados estruturados
    necessários para o envio do WhatsApp.
    """
    chamados_limpos = []
    
    for chamado in lista_chamados_brutos:
        # Uso do .get() é uma prática defensiva essencial em integrações
        # Se a chave não existir, retorna None em vez de quebrar o script
        id_chamado   = chamado.get('2')   # ID do Chamado
        titulo       = chamado.get('1')   # Título (Assunto)
        id_tecnico   = chamado.get('5')   # Técnico atribuído
        status       = chamado.get('12')  # Status (ID ou texto se expand_dropdowns=True)
        requerente  = buscar_nome_usuario(chamado.get('4'))   # Nome do Requerente (Usuário)
        setor      = chamado.get('83').split('> ')[-1]    # Localização (Setor/Departamento)
        
        # Ignora registros que por algum motivo vieram sem ID
        if not id_chamado: continue
            
        chamados_limpos.append({
            "id_chamado": id_chamado,
            "titulo": titulo,
            "id_tecnico": id_tecnico,
            "status": status,
            "requerente": requerente,
            "setor": setor
        })
        
    return chamados_limpos

def buscar_nome_usuario(user_id):
    """
    Busca os detalhes de um usuário específico pelo ID.
    """

    headers = {
        "Content-Type": "application/json",
        "Session-Token": obter_token_cache()
    }
    if APP_TOKEN: headers["App-Token"] = APP_TOKEN

    try:
        url_base_limpa = GLPI_API_URL.rstrip('/')
        url = f"{url_base_limpa}/User/{user_id}" # Endpoint: /User/:id
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dados_usuario = response.json()
            # O GLPI retorna 'firstname' e 'realname' (sobrenome)
            nome = dados_usuario.get('firstname', '')
            sobrenome = dados_usuario.get('realname', '')
            return f"{nome} {sobrenome}".strip() or dados_usuario.get('name') # 'name' é o login
        
        return f"Usuário ID {user_id}"
    except Exception: return "ERRO ao buscar nome"

def mensagem_para_tecnico(chamado, tecnico_info, id_tec):
    """ Organiza a mensagem que será enviada para o técnico """
    telefone = tecnico_info.get('telefone')
    nome = tecnico_info.get('nome_completo')
    id_chamado = chamado['id_chamado']

    if id_tec in [825]:
        registrar_notificacao(id_chamado, id_tec)
        return True

    enviar = f'ENVIAR Chamado {id_chamado} para {nome} ({telefone}). >>>'

    # === AQUI ENTRARÁ A EVOLUTION API ===
    texto_msg = (
        f"🆕 *Novo chamado atribuído {nome}!*\n\n"
        f"✍ Requerente: {chamado['requerente']}\n"
        f"📌 Localização/Setor: {chamado['setor']}\n\n"
        f"🆔 *ID:* {id_chamado}\n"
        f"▶ *Título:* {chamado['titulo']}\n\n"
        f"Link para o chamado:\n"
        f"suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
    )

    sucesso = enviar_mensagem_whatsapp(telefone, texto_msg)

    if sucesso:
        logging.info(f'{enviar} Mensagem entregue.')
        registrar_notificacao(id_chamado, id_tec)
        return True
    else: 
        logging.error(f'{enviar} Falha no envio.')
        return False

def verificar_status_chamado(id):
    """ Verifica se um chaamdo foi solucionado ou excluído """
    url = f'{GLPI_API_URL}/Ticket/{id}'

    headers = {
        "Content-Type": "application/json",
        "Session-Token": obter_token_cache()
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status = data.get('status')

            if data.get('is_deleted') == 1 or status in [5, 6]:
                logging.info(f'- - - Chamado {id} finalizado ou excluído no GLPI! - - -')
                deletar_chamado(id)
                return status
            
        elif response.status_code == 404:
            deletar_chamado(id)
            logging.info(f' - - - Chamado {id} não encontrado (404) - - - ')
            return 0
        
    except Exception as e: logging.error(f'-> ERRO na consulta do chamado {id}: {e}')
    return 1

