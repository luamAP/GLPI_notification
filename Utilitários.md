# Comandos Docker

## **Comandos Essenciais para Manutenção (Cheat Sheet)**

| Comando Docker | O que faz | Quando usar no dia a dia |
| :---- | :---- | :---- |
| docker compose up \-d \--build | Constrói a imagem lendo o código novo e sobe o serviço em segundo plano. | Sempre que você fizer um git pull com código novo ou alterar o .env. |
| docker compose down | Desliga o contêiner e remove a rede virtual associada a ele. | Quando precisar parar a automação completamente para manutenção no servidor. |
| docker ps | Lista apenas os contêineres que estão rodando no momento. | Para verificar o "batimento cardíaco" do seu robô (ver se ele não morreu). |
| docker ps \-a | Lista TODOS os contêineres (mesmo os que deram erro e pararam). | Útil para troubleshooting de contêineres que sobem e caem imediatamente. |
| docker logs \-f automacao-worker | Mostra a saída do terminal do Python em tempo real. | Para monitorar as execuções, ver os logging.info e caçar erros. |
| docker exec \-it automacao-worker bash | Abre um terminal (shell) por dentro do contêiner rodando. | Para investigar se um arquivo foi copiado corretamente ou testar o ping *de dentro* do Docker. |
| docker system prune \-a | **\[CUIDADO\]** Apaga contêineres parados, redes sem uso e imagens antigas. | Quando o disco do servidor Linux começar a ficar cheio (limpeza de faxina). |

---

## **Boas Práticas de Ouro na Infraestrutura**

Para você que está se desenvolvendo e trazendo automação de alto nível para o seu setor, leve esses três mantras para a sua carreira:

**1\. Contêineres são gado, não pets (Imutabilidade)**

Nunca use o comando docker exec para entrar no contêiner e editar o arquivo main.py lá dentro usando o nano ou o vim só para "testar uma coisinha rápida". Se o contêiner reiniciar, sua alteração é apagada. O fluxo correto é sempre: edite o código na sua máquina \-\> suba para o Git \-\> faça o pull no servidor \-\> rode o \--build.

**2\. Cuidado com o "Lixo Espacial" (Gerenciamento de Disco)**

Toda vez que você roda um \--build, o Docker baixa dependências e cria uma imagem nova. A imagem antiga fica lá no HD do Linux, sem nome (chamada de \<none\>), ocupando espaço. Se você faz muitas atualizações, em poucos meses o HD do servidor lota e tudo para. Crie o hábito de rodar o docker system prune \-a (ou sem o \-a para ser menos agressivo) a cada poucos meses para limpar esse lixo.

**3\. O Log é a Única Fonte da Verdade**

Quando a automação falhar (e um dia ela vai, seja por mudança na API, queda de energia ou alteração de layout), nunca tente adivinhar o motivo. Vá direto para o docker logs. A forma como desenhamos as mensagens de logging.critical no seu main.py garante que o seu sistema sempre vai "gritar" exatamente em qual linha o problema aconteceu.

Foi um prazer ajudar a desenhar essa arquitetura. Você tem uma base incrivelmente sólida nas mãos\!
