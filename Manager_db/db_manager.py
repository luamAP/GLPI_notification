import sqlite3
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "automacao_glpi.db"

def conectar():
    """Cria a conexão com o banco de dados SQLite."""
    return sqlite3.connect(DB_FILE)

def criar_tabelas():
    """Cria a tabela de controle de chamados se ela não existir."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    # Criamos uma tabela simples. A chave primária é o próprio ID do chamado.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados_notificados (
            id_chamado INTEGER,
            id_tecnico INTEGER,
            data_notificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_chamado, id_tecnico)
        )
    """)
    conexao.commit()
    conexao.close()

def verificar_notificacao(id_chamado, id_tecnico):
    """Verifica se um chamado já está no banco de dados."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT 1 FROM chamados_notificados WHERE id_chamado = ? AND id_tecnico = ?", (id_chamado,id_tecnico))
    resultado = cursor.fetchone()
    
    conexao.close()
    
    # Se resultado for None, não foi notificado. Se tiver algo, já foi.
    return resultado is not None

def registrar_notificacao(id_chamado, id_tecnico):
    """Registra que um chamado foi notificado."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    try:
        cursor.execute("INSERT INTO chamados_notificados (id_chamado, id_tecnico) VALUES (?, ?)", (id_chamado, id_tecnico))
        conexao.commit()
    except sqlite3.IntegrityError:
        logging.error(f">>> Aviso: O técnico {id_tecnico} já foi notificado sobre o chamado #{id_chamado}. <<<")
    finally:
        conexao.close()

def deletar_chamado(id):
    """Deleta um chamado específico"""
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        # Altere a query para filtrar apenas pelo id_chamado
        sql = "DELETE FROM chamados_notificados WHERE id_chamado = ?"
        
        # O argumento deve ser uma tupla: (valor,)
        cursor.execute(sql, (id,))
        
        conexao.commit()
        
    except Exception as e:
        conexao.rollback()
        logging.error(f'>>> Falha ao deletar o chamado {id}: {e} <<<')

    finally: conexao.close()

def sincronizar_base_notificacoes():
    """Percorre a tabela local"""
    conexao = conectar()
    cursor = conexao.cursor()
    chamados = []

    try:
        # Buscamos apenas IDs únicos para não consultar a API várias vezes para o mesmo chamado
        cursor.execute("SELECT DISTINCT id_chamado FROM chamados_notificados")
        chamados = cursor.fetchall() # Retorna uma lista de tuplas: [(101,), (102,)]


    except Exception as e: 
        if "no such table" in str(e): logging.info(f'A tabela está vazia. Nada para sincronizar no momento.')
        else: logging.critical(f"Falha na sincronização: {e}")
    finally: conexao.close()
    return chamados

# Bloco de teste local
if __name__ == "__main__":
    criar_tabelas()
