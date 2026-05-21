import sqlite3
import logging
import os
from db_manager import conectar
from contatos_manager import formatar_numero

logging.basicConfig(level=logging.INFO, format='[%(levelname)s]: %(message)s')

def importar_base_externa(caminho_db_externo):
    """
    Lê contatos de um arquivo .db externo, higieniza os números
    e atualiza a tabela contatos_requerentes da aplicação.
    """
    if not os.path.exists(caminho_db_externo):
        logging.error(f"Arquivo externo {caminho_db_externo} não foi encontrado!")
        return

    # 1. Conecta no banco de dados de origem (externo)
    conn_externo = sqlite3.connect(caminho_db_externo)
    cursor_ext = conn_externo.cursor()
    
    try:
        # Supondo que a tabela externa se chame 'usuarios_glpi' ou similar. 
        # Ajuste o nome da tabela e colunas conforme o seu arquivo de origem.
        cursor_ext.execute("SELECT id_glpi, nome, usuario, telefone FROM usuarios")
        contatos_externos = cursor_ext.fetchall()
    except Exception as e:
        logging.critical(f"Falha ao ler o banco externo: {e}")
        conn_externo.close()
        return

    # 2. Conecta no banco de dados de destino (sua automação)
    conn_local = conectar()
    cursor_local = conn_local.cursor()

    query_upsert = """
        INSERT INTO contatos_requerentes (id_glpi, nome, usuario, telefone)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id_glpi)
        DO UPDATE SET 
            nome = excluded.nome,
            usuario = excluded.usuario,
            telefone = excluded.telefone
    """

    sucesso = 0
    erros = 0

    for id_glpi, nome, usuario, tel_bruto in contatos_externos:
        try:
            # Garante que o telefone entre no banco local perfeitamente limpo e padronizado
            tel_limpo = formatar_numero(tel_bruto) if tel_bruto else None
            
            cursor_local.execute(query_upsert, (id_glpi, nome.strip(), usuario.strip(), tel_limpo))
            sucesso += 1
        except Exception as e:
            logging.warning(f"Erro ao tratar/inserir requerente ID {id_glpi}: {e}")
            erros += 1

    # 3. Comita as alterações e fecha as conexões
    conn_local.commit()
    conn_local.close()
    conn_externo.close()

    logging.info(f"--- Processo de Importação Concluído ---")
    logging.info(f"✓ Sucesso (Inseridos/Atualizados): {sucesso}")
    logging.info(f"✗ Falhas puladas por erro de formato: {erros}")

if __name__ == "__main__":
    # Exemplo de uso: passe o caminho do arquivo .db que contém os dados novos
    caminho_origem = "dados/novos_cadastros.db"
    importar_base_externa(caminho_origem)