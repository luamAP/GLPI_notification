import requests
import os
from dotenv import load_dotenv

import base64
import json

from Manager_db.db_manager import criar_tabelas, verificar_notificacao, registrar_notificacao, deletar_chamado, sincronizar_base_notificacoes
from Manager_db.contatos_manager import obter_numero_tecnico

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
    try:
        with open (ARQUIVO_SESSAO, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
    
def salvar_token_cache(token):
    with open(ARQUIVO_SESSAO, 'w') as f:
        f.write(token)

def iniciar_sessao_glpi(forcar_novo=False):
    """
    Tenta autenticar na API do GLPI e retornar o token de sessão.
    """
    if not forcar_novo:
        token_cache = obter_token_cache()
        if token_cache:
            print(f'Usando token de sessão em cache: {token_cache[:10]}... ', end=" ")
            return token_cache

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
    
    print("Gerando NOVA sessão no GLPI...", end=' ')
    
    try:
        # Endpoint para iniciar a sessão
        url = f"{GLPI_API_URL}/initSession"
        response = requests.get(url, headers=headers)
        
        # Levanta uma exceção se o status HTTP for um erro (4xx ou 5xx)
        response.raise_for_status() 
        
        session_token = response.json().get("session_token")
        print(f"Sucesso! Sessão iniciada. Novo Token: {session_token[:10]}")
        salvar_token_cache(session_token)
        return session_token
        
    except requests.exceptions.RequestException as erro:
        print(f"ERRO grave de conexão: {erro}\n")
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
        print(f"ERRO ao buscar chamados: {erro}\n")
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
        print(f"ERRO: O arquivo {caminho_arquivo} não foi encontrado.\n")
        return {}
    except json.JSONDecodeError:
        print("ERRO: Falha ao decodificar o arquivo JSON. Verifique a formatação.\n")
        return {}

def mensagem_para_tecnico(chamado, tecnico_info, id_tec):
    telefone = tecnico_info.get('telefone')
    nome = tecnico_info.get('nome_completo')
    id_chamado = chamado['id_chamado']

    print(f'-> [ENVIAR ZAP] Chamado {id_chamado} ("{chamado['titulo']}") para {nome} ({telefone}).')

    # === AQUI ENTRARÁ A EVOLUTION API ===
    texto_msg = (
        f"⚠️ *NOVO CHAMADO ATRIBUÍDO!*\n\n"
        f"🔹 *ID:* {id_chamado}\n"
        f"🔹 *Título:* {chamado['titulo']}\n\n"
        f"Link para o chamado:\n"
        f"https://suporteseminf.manaus.am.gov.br/front/ticket.form.php?id={id_chamado}"
    )

    sucesso = enviar_mensagem_whatsapp(telefone, texto_msg)

    if sucesso:
        print(f'-> Mensagem entregue com sucesso para {nome}.\n')
        registrar_notificacao(id_chamado, id_tec)
        return True
    else: 
        print(f'-> Falha no envio para {nome}. O chamado NÃO foi registrado no banco local e será tentado na próxima rodada.\n')
        return 

def verificar_status_chamado(id):
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
                print(f'- - - Chamado {id} finalizado ou excluído no GLPI! - - -')
                deletar_chamado(id)
                return status
            
        elif response.status_code == 404:
            deletar_chamado(id)
            print(f' - - - Chamado {id} não encontrado (404) - - - ')
            return 0
        
    except Exception as e: print(f'-> ERRO na consulta do chamado {id}: {e}')
    return 1


if __name__ == "__main__":
    sessao = iniciar_sessao_glpi()
    
    if not sessao: print("Falha ao tentar conectar com o GLPI!")
    else:
        try: chamados = buscar_chamados_recentes(sessao)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (401, 403):
                print('Sessão em cache expirou ou é inválida, Renovando...')
                sessao = iniciar_sessao_glpi(forcar_novo=True)
                chamados = buscar_chamados_recentes(sessao)
            else: raise e

        if chamados:
            chamados_padronizados = processar_chamados_brutos(chamados)
            mapa_tecnicos = carregar_mapa_tecnicos()

            print("\n--- INICIANDO CRUZAMENTO DE DADOS ---\n")
            # Cria tabela de notificação
            criar_tabelas()

            for chamado in chamados_padronizados:
                # Avalia ANTES de corverter para string
                if chamado['id_tecnico'] is None:
                    print(f'-> [INFO] Chamado {chamado['id_chamado']} está Novo/Sem técnico. Aguardando triagem.')

                id_tec = str(chamado['id_tecnico']) # Garantindo que é string para buscar no JSON
                id_chamado = chamado['id_chamado']

                if verificar_notificacao(id_chamado, id_tec):
                    print(f'-> [INFO] Chamado {id_chamado} já foi notificado para o técnico {id_tec}. Ignorando.')
                    continue

                tecnico_info = obter_numero_tecnico(id_tec)

                # Se o chamado não tem técnico atribuído (None), não há para quem enviar mensagem.
                if tecnico_info: mensagem_para_tecnico(chamado, tecnico_info, id_tec)

                else: print(f'-> [ERRO] Técnico ID {id_tec} não encontrado no JSON. Chamado {id_chamado} retido.')

        else: print("\nNenhum chamado retornado.")
        
        chamados = sincronizar_base_notificacoes()
        for (id_chamado,) in chamados: verificar_status_chamado(id_chamado)

        # COM LIST COMPREHENSION
        # # Busca os IDs e já executa a verificação/deleção para cada um em uma linha
        # [verificar_status_chamado(id_ch[0]) for id_ch in sincronizar_base_notificacoes()]

        print(f'Finalizando Varredura...\n')
        
