import json
import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_TECNICOS = os.path.join(BASE_DIR, '..', "tecnicos.json")

def carregar_contatos():
    """Lê o arquivo JSON e retorna o dicionário de técnicos."""
    if not os.path.exists(ARQUIVO_TECNICOS):
        logging.error(f"Arquivo {ARQUIVO_TECNICOS} não encontrado!")
        return {}
        
    try:
        with open(ARQUIVO_TECNICOS, 'r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError:
        logging.error(f"O arquivo {ARQUIVO_TECNICOS} possui erros de formatação (JSON inválido).")
        return {}
    except FileNotFoundError:
        logging.error(f'O arquivo {ARQUIVO_TECNICOS} não foi encontrado.')
        return {}

def obter_numero_tecnico(identificador_glpi):
    """Busca o número de WhatsApp de um técnico específico."""
    contatos = carregar_contatos()
    
    # O método .get() é seguro: retorna None se a chave não existir
    numero = contatos.get(identificador_glpi)
    
    if identificador_glpi is None: return None 
    elif numero: return numero
    else:
        logging.info(f"Aviso: Técnico '{identificador_glpi}' não encontrado no mapeamento JSON.")
        return None

def formatar_numero(telefone):
    # 1. Limpeza bruta
    numero = "".join(filter(str.isdigit, str(telefone)))

    # 2. Normalização de DDD (Caso venha apenas 8 ou 9 dígitos)
    if len(numero) in (8, 9):
        numero = "92" + numero  # Exemplo de DDD padrão

    # 3. Normalização de DDI (Se não tem o 55, adiciona)
    if not numero.startswith('55'):
        numero = '55' + numero

    # 4. Validação Final (Se após as tentativas o tamanho for bizarro, aí sim erro)
    if len(numero) not in (12, 13):
        logging.error(f"Número {telefone} resultou em formato inválido: {numero}")
        raise ValueError(f"Telefone fora do padrão: {numero}")

    return numero

if __name__=="__main__":
    pass
