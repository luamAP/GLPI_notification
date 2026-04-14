import sqlite3
import os

DB_FILE = "automacao_glpi.db"

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
            id_chamado INTEGER PRIMARY KEY,
            data_notificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conexao.commit()
    conexao.close()
    print("Banco de dados verificado/inicializado com sucesso.")

def foi_notificado(id_chamado):
    """Verifica se um chamado já está no banco de dados."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT 1 FROM chamados_notificados WHERE id_chamado = ?", (id_chamado,))
    resultado = cursor.fetchone()
    
    conexao.close()
    
    # Se resultado for None, não foi notificado. Se tiver algo, já foi.
    return resultado is not None

def registrar_notificacao(id_chamado):
    """Registra que um chamado foi notificado."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    try:
        cursor.execute("INSERT INTO chamados_notificados (id_chamado) VALUES (?)", (id_chamado,))
        conexao.commit()
        print(f"Chamado #{id_chamado} registrado no banco com sucesso.")
    except sqlite3.IntegrityError:
        print(f"Aviso: Tentativa de registrar o chamado #{id_chamado} em duplicidade.")
    finally:
        conexao.close()

# Bloco de teste local
if __name__ == "__main__":
    criar_tabelas()
    
    # Simulando a lógica de triagem
    chamado_teste = 5501
    
    if not foi_notificado(chamado_teste):
        print(f"Enviando WhatsApp para o chamado {chamado_teste}...")
        # Aqui entraria o código da Evolution API no futuro
        registrar_notificacao(chamado_teste)
    else:
        print(f"Chamado {chamado_teste} já havia sido notificado. Ignorando.")