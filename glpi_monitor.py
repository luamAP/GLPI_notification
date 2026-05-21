import requests
import os
from dotenv import load_dotenv
import logging

import base64

from Manager_db.db_manager import registrar_notificacao, deletar_chamado, verificar_notificacao, telefone_do_requerente, status_chamado
from Evolution_API.criar_instancia import enviar_mensagem_whatsapp
# from Manager_db.contatos_manager import obter_numero_tecnico
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
    
    if obter_token_cache() is None: 
        logging.warning("Token de sessão não encontrado. Iniciando a sessão primeiro.")
        iniciar_sessao_glpi()

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
        logging.info(f"Sucesso! Sessão iniciada. Novo Token: {session_token[:5]}...")
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
    # for chamado in lista_chamados_brutos:
    for i in range(len(lista_chamados_brutos)):
        chamado = lista_chamados_brutos[i]
        try: 
            dados_requerente = buscar_usuario(chamado.get('4')) # Nome do Requerente (Usuário)
            id_tecnico = chamado.get('5') # Nome do técnico (Usuário)
            if id_tecnico is None: dados_tecnico = None
            elif type(id_tecnico) is list: dados_tecnico = list(map(buscar_usuario, id_tecnico))
            else: dados_tecnico = [buscar_usuario(id_tecnico)] # Nome do técnico (Usuário)

            # Uso do .get() é uma prática defensiva essencial em integrações
            # Se a chave não existir, retorna None em vez de quebrar o script
            id_chamado   = chamado.get('2')   # ID do Chamado
            titulo       = chamado.get('1')   # Título (Assunto)
            status       = chamado.get('12')  # Status (ID ou texto se expand_dropdowns=True)
            setor      = chamado.get('83').split('> ')[-1]    # Localização (Setor/Departamento)
            
            # Ignora registros que por algum motivo vieram sem ID
            if not id_chamado: continue
                
            chamados_limpos.append({
                "id_chamado": id_chamado,
                "titulo": titulo,
                "dados_tecnico": dados_tecnico,
                "status": status,
                "dados_requerente": dados_requerente,
                "setor": setor
            })
        except Exception as erro: raise erro
    return chamados_limpos

def buscar_usuario(user_id, buscar=False):
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

            if buscar=="nome":
                # O GLPI retorna 'firstname' e 'realname' (sobrenome)
                nome = dados_usuario['firstname']
                sobrenome = dados_usuario['realname']
                return f"{nome} {sobrenome}".strip() or dados_usuario['name'] # 'name' é o login

            if buscar=="celular":
                celular = dados_usuario['mobile']
                return celular or None
            else:
                dados_usuario = {
                    'id': dados_usuario.get('id'),
                    'usuario': dados_usuario.get('name'),
                    'telefone': dados_usuario.get('mobile'),
                    'nome': dados_usuario.get('firstname')+' '+dados_usuario.get('realname'),
                    'localizacao': dados_usuario.get('location')
                }

                return dados_usuario

        else: logging.error(f"ERRO ao buscar usuário {user_id}: Status {response.status_code}")
    except Exception as e: logging.error(f"ERRO ao buscar nome.\n{e}")

def mensagem_para_tecnico(chamado, tecnico_info):
    """ Organiza a mensagem que será enviada para o técnico """
    try:
        if tecnico_info is None: return False
        requerente_info = chamado['dados_requerente']
        
        id_chamado = chamado['id_chamado']
        setor = chamado['setor']
        titulo = chamado['titulo']
        id_tec = tecnico_info['id']
        nome = tecnico_info['nome']
        telefone = tecnico_info['telefone']
        requerente = requerente_info['nome']

        enviar = f'ENVIAR Chamado {id_chamado} para {nome} ({telefone}). >>>'

        # === AQUI ENTRARÁ A EVOLUTION API ===
        texto_msg = (
            f"🆕 *Novo chamado atribuído {nome}!*\n\n"
            f"✍ Requerente: {requerente}\n"
            f"📌 Localização/Setor: {setor}\n\n"
            f"🆔: {id_chamado}\n"
            f"▶ *Título:* {titulo}\n\n"
            f"Link para o chamado:\n"
            f"suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
        )
        if not telefone is None: sucesso = enviar_mensagem_whatsapp(telefone, texto_msg)
        else: return False
        
        if sucesso:
            logging.info(f'{enviar} Mensagem entregue.')
            registrar_notificacao(id_chamado, id_tec)
            return True
        else: 
            logging.error(f'{enviar} Falha no envio.')
            return False
    except Exception as e: logging.error(f'ERRO ao organizar mensagem para técnico: {e}')

def mensagem_para_requerente(id_chamado, id_req, status, tecnico):
    """ Organiza a mensagem que será enviada para o requerente """
    try:
        dados_banco = telefone_do_requerente(id_req)
        if dados_banco is None: return "CONTATO VAZIO"

        telefone, requerente = dados_banco
        enviar = f'NOTIFICAR REQUERENTE {requerente} do chamado {id_chamado} ({telefone}). >>>'

        # === AQUI ENTRARÁ A EVOLUTION API ===
        if status==2: 
            texto_msg = (
                f"🟢*Chamado atribuído!*\n\n"
                f"👩‍💻👨‍💻 Técnico/Analista:\n{tecnico}\n"
                f"🆔: {id_chamado}\n\n"
                f"Link para o chamado:\n"
                f"suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
            )
        elif status==4: 
            texto_msg = (
                f"⚠*Chamado pendente de informação!*\n\n"
                f"🆔: {id_chamado}\n\n"
                f"Seu chamado precisa da sua atenção!\n"
                f"suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
            )
        elif status==5: 
            texto_msg = (
                f"*Chamado solucionado!*\n\n"
                f"🆔: {id_chamado}\n\n"
                f"Verifique a resolução do chamado. Aprove✅ ou Recuse❌.\n"
                f"suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
            )
        sucesso = enviar_mensagem_whatsapp(telefone, texto_msg)
        
        if sucesso:
            logging.info(f'{enviar} Mensagem entregue.')
            registrar_notificacao(id_chamado, status, False)
            return "SUCESSO"
        else: 
            logging.error(f'{enviar} Falha no envio.')
            return "FALHA"
    except Exception as e: 
        logging.error(f'ERRO ao organizar mensagem para o requerente: {e}')
        return "ERRO INTERNO"

def verificar_status_chamado(id):
    """ Verifica se um chaamdo foi solucionado ou excluído """
    url_ticket = f'{GLPI_API_URL}/Ticket/{id}'
    url_ticket_requerente = f'{GLPI_API_URL}/Ticket/{id}/Ticket_User'

    headers = {
        "Content-Type": "application/json",
        "Session-Token": obter_token_cache()
    }

    try:
        response = requests.get(url_ticket, headers=headers)

        if response.status_code == 404:
            deletar_chamado(id,"chamados_notificados")
            logging.info(f' - - - Chamado {id} não encontrado (404) - - - ')
            return 0
    
        elif response.status_code == 200:
            data = response.json()
            status = data.get('status')
            status_no_banco = status_chamado(id)
            # Registrar o chamado na tabela notificacoes_requerentes

            if data.get('is_deleted') == 1 or status in [5, 6]:
                logging.info(f'- - - Chamado {id} finalizado ou excluído no GLPI! - - -')
                deletar_chamado(id,"chamados_notificados")
            if status == 1 and status!=status_no_banco:
                logging.info(f'- - - Chamado {id} "desatribuído"! - - -')
                deletar_chamado(id,"chamados_notificados")
            if status == 4 and status_no_banco!=status: logging.info(f'- - - Chamado {id} pendente de informação! - - -')

        else: logging.critical(f'ERRO DESCONHECIDO {response.status_code}: {response}')
        
    except Exception as e: logging.error(f'-> ERRO na consulta do chamado {id}: {e}')
    
    enviado = "IGNORADO"
    if (status in [2,4,5,6]) and (status_no_banco!=status): 
        try: 
            response = requests.get(url_ticket_requerente, headers=headers)
            id_requerente = None
            if response.status_code == 200:
                usuarios = response.json()
                for user in usuarios: 
                    if user.get('type')==1: 
                        id_requerente = user.get('users_id')
                        break
            elif response.status_code == 404: logging.info(f'ERRO 404 ao buscar o id do requerente')
        except Exception as e: logging.error(f'--> ERRO na consulta do requerente do chamado {id}')
        if not id_requerente is None: enviado = mensagem_para_requerente(id, id_requerente, status, None)
    if status==5 and enviado in ["SUCESSO", "SEM CONTATO", "IGNORADO"]: 
        logging.info(f'Excluindo chamado #{id} das notificações dos requerentes (MOTIVO: {enviado})')
        deletar_chamado(id, "notificacoes_requerentes")

    return status

def chamado_notificado(chamado, dados_tec):
    id_chamado = chamado['id_chamado']
    id_tec = dados_tec['id']
    # Verificar o chamado "verificar_notificacao(id_chamado, id_tech)"
    try:
        if not verificar_notificacao(id_chamado, id_tec) is None: return True
        else: 
            mensagem_para_tecnico(chamado, dados_tec)
            # Enviar mensagem para o requerente também
            if verificar_notificacao(id_chamado) is None: mensagem_para_requerente(chamado['id_chamado'], 
                                    chamado['dados_requerente']['id'], 
                                    chamado['status'], dados_tec['nome'])
    except Exception as e: logging.error(e)

if __name__=="__main__":
    verificar_status_chamado(10167)
    pass
