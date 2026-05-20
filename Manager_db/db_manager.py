import sqlite3
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "dados" / "automacao_glpi.db"

def conectar():
    """Cria a conexão com o banco de dados SQLite."""
    return sqlite3.connect(DB_FILE)

def criar_tabelas():
    """Cria a tabela de controle de chamados se ela não existir."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados_notificados (
            id_chamado INTEGER,
            id_tecnico INTEGER,
            data_notificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_chamado, id_tecnico)
        )
    """)

    # Tabela para armazenar os contatos manuais dos requerentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contatos_requerentes (
            id_glpi INTEGER PRIMARY KEY,
            nome TEXT,
            usuario TEXT,
            telefone TEXT
        )
    """)

    # Tabela para controlar o que já foi enviado ao requerente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes_requerentes (
            id_chamado INTEGER PRIMARY KEY,
            status INTEGER,
            data_notificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conexao.commit()
    conexao.close()

def verificar_notificacao(id_chamado, id_tecnico=None):
    """Verifica se um chamado já está no banco de dados."""
    conexao = conectar()
    cursor = conexao.cursor()
        
    try:
        if id_tecnico: cursor.execute("SELECT 1 FROM chamados_notificados WHERE id_chamado = ? AND id_tecnico = ?", (id_chamado,id_tecnico))
        else: cursor.execute("SELECT 1 FROM notificacoes_requerentes WHERE id_chamado = ?", (id_chamado,))
        resultado = cursor.fetchone()
    except Exception as e:
        logging.error(f"Erro ao verificar notificação para o chamado {id_chamado} e técnico {id_tecnico}: {e}")
        resultado = None
    finally: conexao.close()
    
    # Se resultado for None, não foi notificado. Se tiver algo, já foi.
    return resultado

def registrar_notificacao(id_chamado, id, tecnico=True):
    """Registra que um chamado foi notificado."""
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        if tecnico: cursor.execute("INSERT INTO chamados_notificados (id_chamado, id_tecnico) VALUES (?, ?)", (id_chamado, id))
        else: 
            # Otimização de Arquitetura: UPSERT do SQLite
            cursor.execute("""
                INSERT INTO notificacoes_requerentes (id_chamado, status, data_notificacao) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id_chamado) 
                DO UPDATE SET status = excluded.status, data_notificacao = CURRENT_TIMESTAMP
            """, (id_chamado, id))
        conexao.commit()
    except sqlite3.IntegrityError:
        if tecnico: logging.error(f">>> Aviso: O técnico {id} já foi notificado sobre o chamado #{id_chamado}. <<<")
        else: logging.error(f">>> Aviso: O requerente do chamado #{id_chamado} já foi notificado. <<<")
    finally:
        logging.info(f'Chamado {id_chamado} registrado para o id {id}')
        conexao.close()

def deletar_chamado(id, nome_do_banco):
    """
    Deleta um chamado/linha específico
    
    nome_do_banco: ["chamados_notificados" | "contatos_requerentes" | "notificacoes_requerentes"]
    """
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        # Altere a query para filtrar apenas pelo id_chamado
        if nome_do_banco=="chamados_notificados": sql = "DELETE FROM chamados_notificados WHERE id_chamado = ?"
        elif nome_do_banco=="notificacoes_requerentes": sql = "DELETE FROM notificacoes_requerentes WHERE id_chamado = ?"
        elif nome_do_banco=='contatos_requerentes': sql = "DELETE FROM contatos_requerentes WHERE id_glpi = ?"

        # O argumento deve ser uma tupla: (valor,)
        cursor.execute(sql, (id,))
        
        conexao.commit()
        
    except Exception as e:
        conexao.rollback()
        logging.error(f'>>> Falha ao deletar o chamado {id}: {e} <<<')

    finally: conexao.close()

def telefone_do_requerente(id_req):
    """Percorre a tabela "contatos_requerente" para buscar o telefone"""
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("SELECT telefone, nome FROM contatos_requerentes WHERE id_glpi = ?", (id_req,))
        resultado = cursor.fetchone()

        if resultado: return resultado
        else: 
            logging.warning(f'Telefone do requerente {id_req} não encontrado no banco de dados')
            return None
    except Exception as e: 
        logging.error(f'>>> Aviso: Requerente {id_req} não encontrado: {e}')
        return None
    finally: conexao.close()

def status_chamado(id_chamado):
    """Percorre a tabela "notificacoes_requerentes" para buscar o status do chamado"""
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("SELECT status FROM notificacoes_requerentes WHERE id_chamado = ?", (id_chamado,))
        status = cursor.fetchone()

        if status: return status[0]
        else:
            logging.warning(f'Chamado ainda não criado: {id_chamado}')
            return None
    except Exception as e: 
        logging.error(f'>>> Aviso: Não foi possível encontrar {id_chamado}: {e}')
        return None
    finally: conexao.close()

def sincronizar_base_notificacoes():
    """Percorre a tabela local"""
    conexao = conectar()
    cursor = conexao.cursor()
    chamados = []

    try:
        # Buscamos apenas IDs únicos para não consultar a API várias vezes para o mesmo chamado
        cursor.execute("""
                       SELECT id_chamado FROM chamados_notificados
                       UNION
                       SELECT id_chamado FROM notificacoes_requerentes
                       """)
        chamados = cursor.fetchall() # Retorna uma lista de tuplas: [(101,), (102,)]

    except Exception as e: 
        if "no such table" in str(e): logging.info(f'A tabela está vazia. Nada para sincronizar no momento.')
        else: logging.critical(f"Falha na sincronização: {e}")
    finally: conexao.close()
    return chamados

# Bloco de teste local
if __name__ == "__main__":
    criar_tabelas()
