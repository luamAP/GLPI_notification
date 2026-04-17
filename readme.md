# Arquitetura do Projeto

Nossa automação atuará como um "middleware" (um intermediário) entre o GLPI e o WhatsApp.

## O fluxo lógico

1. Monitoramento: O script Python irá consultar o GLPI periodicamente em busca de chamados recentes que tenham recebido atribuição de um técnico.

2. Triagem: O código vai verificar se este chamado já foi notificado anteriormente (para não mandar mensagens duplicadas e irritar a equipe).

3. Mapeamento: O script cruzará o nome ou ID do técnico atribuído com o seu respectivo número de WhatsApp.

4. Notificação: Disparo da mensagem padronizada no privado do técnico.

## Plano de Desenvolvimento Passo a Passo

- [x] Fase 1: Prova de Conceito com a API do GLPI. Configurar tokens de acesso, conectar via Python e conseguir listar os chamados abertos/atribuídos.
  - [x] Configurar APIs do GLPI (App-Token e User-Token)
  - [x] Contornar o bloqueio de rede implementando o proxy corporativo direto no script Python.
  - [x] Validar a extração da lista de chamados atribuídos

- [x] Fase 2: Estruturação de Dados e Lógica de Estado.
  - [x] Criar a "memória" das notificações (Banco de Dados SQLite via `db_manager.py`).
  - [x] Mapeamento de técnicos (Criar o arquivo `tecnicos.json` e isolá-lo no `.gitignore`).
  - [x] Implementar o gerenciador de contatos (`contatos_manager.py`).

- [x] Fase 3: Integração com WhatsApp. Definir e implementar o serviço para envio da mensagem.
  - [x] Subir a Evolution API v2 via Docker (com PostgreSQL e Redis).
  - [x] Configurar o túnel de Proxy Corporativo no `.env` do Docker para acesso à internet.
  - [x] Criar scripts de automação para criação e conexão de instâncias (`criar_instancia.py` e `conectar_instancia.py`).
  - [x] Escanear QR Code e estabilizar a sessão do WhatsApp.

- [x] Fase 4: Orquestração e Deploy (Loop Final).
  - [x] Unir as Fases 1, 2 e 3 em um único script `main.py`.
  - [x] Criar o loop de repetição (ex: rodar a cada 5 minutos) feita pelo Agendador de tarefas do Windows.
  - [x] Implementar tratamento de exceções (quedas de internet, GLPI fora do ar).
  - [x] Colocar para rodar em background no servidor/máquina local.
  