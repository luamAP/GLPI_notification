import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_TECNICOS = os.path.join(BASE_DIR, '..', "tecnicos.json")

def carregar_contatos():
    """Lê o arquivo JSON e retorna o dicionário de técnicos."""
    if not os.path.exists(ARQUIVO_TECNICOS):
        print(f"Erro: Arquivo {ARQUIVO_TECNICOS} não encontrado!")
        return {}
        
    try:
        with open(ARQUIVO_TECNICOS, 'r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {ARQUIVO_TECNICOS} possui erros de formatação (JSON inválido).")
        return {}
    except FileNotFoundError:
        print(f'ERRO: O arquivo {ARQUIVO_TECNICOS} não foi encontrado.')
        return {}

def obter_numero_tecnico(identificador_glpi):
    """Busca o número de WhatsApp de um técnico específico."""
    contatos = carregar_contatos()
    
    # O método .get() é seguro: retorna None se a chave não existir
    numero = contatos.get(identificador_glpi)
    
    if identificador_glpi is None: return None 
    elif numero: return numero
    else:
        print(f"Aviso: Técnico '{identificador_glpi}' não encontrado no mapeamento.")
        return None

# Bloco de teste
if __name__ == "__main__":
    pass