import logging
from glpi_monitor import check_api, obter_token_cache, buscar_chamados_recentes, processar_chamados_brutos, verificar_status_chamado, chamado_notificado
from Manager_db.db_manager import criar_tabelas, DB_FILE, sincronizar_base_notificacoes
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
        # Cria tabela de notificação
        if not os.path.exists(DB_FILE): criar_tabelas()

        for chamado in processar_chamados_brutos(chamados):
            tec_id = chamado['id_tecnico']
            # Avalia ANTES de corverter para string
            if tec_id is None: continue

        # Transformar tudo em lista para iterar de uma vez
            tecnicos = tec_id if isinstance(tec_id, list) else [tec_id]

            for tec in tecnicos:
                # verificar_mudanca_tecnica(id_chamado)
                chamado_notificado(chamado, str(tec))

    else: logging.debug(f'Nenhum chamado encontrado!')
    
    chamados = sincronizar_base_notificacoes()
    # print(chamados)
    for (id_chamado,) in chamados: 
        verificar_status_chamado(id_chamado)

    # COM LIST COMPREHENSION
    # # Busca os IDs e já executa a verificação/deleção para cada um em uma linha
    # [verificar_status_chamado(id_ch[0]) for id_ch in sincronizar_base_notificacoes()]

if __name__ == "__main__":
    executar_monitoramento()