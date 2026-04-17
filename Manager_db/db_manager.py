import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "automacao_glpi.db")

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
    print(">>> Banco de dados verificado/inicializado com sucesso. <<<\n")

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
        print(f">>> Chamado #{id_chamado} registrado para o técnico {id_tecnico} no banco com sucesso. <<<")
    except sqlite3.IntegrityError:
        print(f">>> Aviso: O técnico {id_tecnico} já foi notificado sobre o chamado #{id_chamado}. <<<")
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
        print(f">>> Total de {cursor.rowcount} técnicos removidos para o chamado {id}. <<<")

    except Exception as e:
        conexao.rollback()
        print(f'>>> [ERRO] Falha ao deletar o chamado {id}: {e} <<<')

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
        if "no such table" in str(e): print(f'[INFO] A tabela está vazia. Nada para sincronizar no momento.')
        else: print(f"[ERRO CRÍTICO] Falha na sincronização: {e}")
    finally: conexao.close()
    return chamados

# Bloco de teste local
if __name__ == "__main__":
    criar_tabelas()
