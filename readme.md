# Arquitetura do Projeto

Nossa automação atuará como um "middleware" (um intermediário) entre o GLPI e o WhatsApp. 

## O fluxo lógico

1. Monitoramento: O script Python irá consultar o GLPI periodicamente em busca de chamados recentes que tenham recebido atribuição de um técnico.

2. Triagem: O código vai verificar se este chamado já foi notificado anteriormente (para não mandar mensagens duplicadas e irritar a equipe).

3. Mapeamento: O script cruzará o nome ou ID do técnico atribuído com o seu respectivo número de WhatsApp.

4. Notificação: Disparo da mensagem padronizada no grupo ou no privado do técnico.

## Plano de Desenvolvimento Passo a Passo

- [ ] Fase 1: Prova de Conceito com a API do GLPI. Configurar tokens de acesso, conectar via Python e conseguir listar os chamados abertos/atribuídos.
  - [x] Configurar APIs do GLPI (Geral e User)
    - [ ] Solicitar a supervisão o acesso pelo firewall da rede  
  
  - [x] Implementar o monitoramento do GLPI

- [ ] Fase 2: Estruturação de Dados e Lógica de Estado. Criar um arquivo de configuração (JSON) relacionando os técnicos aos seus números e criar um banco de dados simples (SQLite) para registrar os chamados já notificados.
  - [x] Criar a "mémoria" das notificações
    - [x] Criar o banco de dados

  - [ ] Mapemaneto de técnicos (números do whastapp)
    - [ ] Criar um .json com o número dos técnicos
    - [x] Adicionar o .json no .gitignore
  
  - [x] Implementar um gerenciador de contatos

- [ ] Fase 3: Integração com WhatsApp. Definir e implementar a biblioteca/serviço para envio da mensagem.
  - [x] Subir a Evolution API
    - [x] Configurar o arquivo *docker-compose.yml*

- [ ] Fase 4: Loop e Deploy. Colocar o script para rodar em background (como um serviço no servidor) de forma contínua e tratar exceções (o que acontece se a internet cair? O script não pode parar de rodar).


