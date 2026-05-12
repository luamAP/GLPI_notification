FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Correção 1: No Docker, separamos arquivos por espaço, não por vírgula.
# O asterisco no uv.lock* previne erros caso o arquivo ainda não tenha sido gerado.
COPY pyproject.toml uv.lock* ./

# Correção 2: O comando uv sync está corretíssimo para instalar as dependências.
RUN uv sync

# Correção 3: O comando para copiar o restante dos arquivos é ponto e espaço ponto.
# Isso significa "copie tudo da pasta atual da minha máquina para a pasta atual do contêiner".
COPY . .

# Correção 4: Como o uv sync cria um ambiente virtual isolado, 
# precisamos usar o 'uv run' para que o Python enxergue as bibliotecas instaladas.
CMD ["uv", "run", "main.py"]