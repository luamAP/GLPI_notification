import logging
from logging.handlers import RotatingFileHandler
from glpi_monitor import check_api, obter_token_cache, buscar_chamados_recentes, processar_chamados_brutos, verificar_status_chamado, chamado_notificado
from Manager_db.db_manager import criar_tabelas, DB_FILE, sincronizar_base_notificacoes, registrar_notificacao, verificar_notificacao, status_chamado
import os, sys
import time
from datetime import datetime, time as dt_time

DB_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s]-%(funcName)s: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        # ALTERE esta linha para apontar dinamicamente para dentro da pasta dados:
        RotatingFileHandler(DB_FILE.parent / "monitor_logs.log", maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def executar_monitoramento():
    try: check_api()
    except Exception as e:
        logging.critical(f"Saúde da API comprometida. Abortando varredura: {e}")
        return # Interrompe a execução antes de tentar buscar chamados
    finally: logging.debug("Testando API (check_api)!")
    chamados = []

    try: chamados = buscar_chamados_recentes(obter_token_cache())
    except Exception as e: logging.error(f"Falha ao tentar conectar com o GLPI! {e}")
    finally: logging.debug("Testando buscar_chamados_recentes!")

    if chamados:
        # Cria tabela de notificação
        if not os.path.exists(DB_FILE): criar_tabelas()

        try: chamados_limpos = processar_chamados_brutos(chamados)
        except Exception as e: logging.error(f'ERRO ao processar dados brutos: {e}')
        for chamado in chamados_limpos:
            # Cria o chamado na tabela notificacoes_requerentes se não existir
            if (verificar_notificacao(chamado['id_chamado']) is None) or (chamado['status']!=status_chamado(chamado['id_chamado'])): registrar_notificacao(chamado['id_chamado'], chamado['status'], False)
            if chamado['dados_tecnico'] is None: logging.info(f'>>> Chamado {chamado["id_chamado"]} sem técnico atribuído. <<<')
            else: 
                for tec in chamado['dados_tecnico']: chamado_notificado(chamado, tec)

    else: logging.debug(f'Nenhum chamado encontrado!')
    
    chamados = sincronizar_base_notificacoes()
    for (id_chamado,) in chamados: verificar_status_chamado(id_chamado)

    # COM LIST COMPREHENSION
    # # Busca os IDs e já executa a verificação/deleção para cada um em uma linha
    # [verificar_status_chamado(id_ch[0]) for id_ch in sincronizar_base_notificacoes()]

if __name__ == "__main__":
    logging.info(f'SISTEMA INICIADO!')
    while True:
        # Se for fim de semana (valores menores que 5) e estiver entre 7:50 - 16:50 
        if (datetime.now().weekday() <= 5) and (dt_time(7,50) <= datetime.now().time() <= dt_time(16,50)): 
            try: executar_monitoramento()
            except Exception as e: logging.critical(f"Erro inesperado no monitoramento: {e}")
        time.sleep(60*5)
    # executar_monitoramento()