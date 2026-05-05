# PARA AJUSTAR

1. [x] Poluição de Logs e processamento redundante
   * Sugestão: Só logue o "Ignorando" se o status do chamado mudar, ou remova essa linha completamente. O log deve focar em ações ou erros.

2. [x] Overhead de Inicialização do Banco de Dados
    * Gargalo: Isso é uma operação de banco de dados desnecessária se o arquivo .db já existe.

3. [x] "Gargalo da Inércia" (Erros 401 - Unauthorized)
   1. O Problema: O script percebe que o token em cache é inválido, mas ele simplesmente encerra a varredura e espera mais 5 minutos para gerar uma nova sessão na rodada seguinte (07:55)

4. [x] Ruído de Rede e Esgotamento de Recursos
   1. Sugestão: Uma verificação simples de "Saúde da API" no início do script (um ping ou um GET /) poderia encerrar a execução imediatamente se a API estiver fora, poupando o processamento de tentar enviar cada chamado individualmente.

5. ~~[ ] Latência de Triagem (O Limbo do "None")~~
   ~~1. Gargalo: O sistema ficou "vigiando" esse chamado por quase 7 horas.~~
   ~~2. Insight: Como seu log agora vai ser mais limpo, talvez valha a pena criar um alerta único ou um log especial: "Chamado X aguardando triagem há mais de 2 horas". Isso ajudaria a identificar se o problema é o sistema de notificação ou se a equipe de suporte humana está sobrecarregada e não está atribuindo os chamados.~~

6. [x] Limpar o código principal.

7. [x] Pegar as informações de nome e setor do requerente

8. [x] Ajustar mensagem para o técnico
   1. [x] Nome do técnico
   2. [x] Nome do requerente
   3. [x] Setor do requerente
   4. [x] Eliminar o https do link

9. [x] Ajustar o log para sair apenas informações necessárias
   1. [x] Eliminar o texto iniciando e finalizando varredura
   2. [x] Colocar data e hora para cada informação do log (ex.: [28/04/2026  9:50:06,70] [INFO] -> [ENVIAR ZAP] Chamado 10038 ("REATIVA��O USU�RIO") para ADRIANO LEITE (+55 92 9532-8630).)
   3. [x] Ajustar a formatação de texto, consertar o erro REATIVA��O USU�RIO
   4. [x] Eliminar logs de confirmação, como `Usando token de sess�o em cache: 1d5t3jp473...  Buscando chamados recentes...`, `-> Mensagem entregue com sucesso para ADRIANO LEITE.`, `>>> Chamado #10038 registrado para o t�cnico 12 no banco com sucesso. <<<`

10. [x] Ajustar execções de chamados
    1. [x] Técnicos duplicados, enviar para os dois
    2. [x] Técnico trocado, atualizar o banco de dados e enviar para o novo técnico

11. [x] Criar um executável para rodar em um servidor
