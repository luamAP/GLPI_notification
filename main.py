import logging
import sys
from glpi_monitor import check_api, obter_token_cache, buscar_chamados_recentes, processar_chamados_brutos, verificar_status_chamado, mensagem_para_tecnico
from Manager_db.db_manager import criar_tabelas, DB_FILE, verificar_notificacao
from Manager_db.contatos_manager import obter_numero_tecnico
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler("monitor_logs.txt", encoding='utf-8')
        # logging.StreamHandler(sys.stdout) # Exibe no terminal também
    ]
)

logger = logging.getLogger(__name__)

def executar_monitoramento():
    try: check_api()
    except Exception as e:
        logging.critical(f"Saúde da API comprometida. Abortando varredura: {e}")
        return # Interrompe a execução antes de tentar buscar chamados
    chamados = []

    try: chamados = buscar_chamados_recentes(obter_token_cache())
    except Exception as e: logging.error(f"Falha ao tentar conectar com o GLPI! {e}")

    if chamados:
        chamados_padronizados = processar_chamados_brutos(chamados)

        # Cria tabela de notificação
        if not os.path.exists(DB_FILE): criar_tabelas()

        for chamado in chamados_padronizados:

            # Avalia ANTES de corverter para string
            if chamado['id_tecnico'] is None: continue

            id_tec = str(chamado['id_tecnico']) # Garantindo que é string para buscar no JSON
            id_chamado = chamado['id_chamado']

            if verificar_notificacao(id_chamado, id_tec): continue

            tecnico_info = obter_numero_tecnico(id_tec)

            # Se o chamado não tem técnico atribuído (None), não há para quem enviar mensagem.
            if tecnico_info: mensagem_para_tecnico(chamado, tecnico_info, id_tec)
            else: logging.error(f'-> Técnico ID {id_tec} não encontrado no JSON. Chamado {id_chamado} retido.')
    else: logging.debug(f'Nenhum chamado encontrado!')
    
    chamados = sincronizar_base_notificacoes()
    for (id_chamado,) in chamados: verificar_status_chamado(id_chamado)

    # COM LIST COMPREHENSION
    # # Busca os IDs e já executa a verificação/deleção para cada um em uma linha
    # [verificar_status_chamado(id_ch[0]) for id_ch in sincronizar_base_notificacoes()]
        
    pass

if __name__ == "__main__":
    executar_monitoramento()