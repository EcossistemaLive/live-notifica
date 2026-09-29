# Live Monitor - Container Docker
# Base com Python 3.11 e dependências do Chromium para Playwright
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Define fuso horário oficial de Brasília
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Instala dependências do Python
COPY engine/requirements.txt /app/engine/requirements.txt
RUN pip install --no-cache-dir -r /app/engine/requirements.txt

# Garante que o navegador Chromium do Playwright está pronto
RUN playwright install chromium

# Copia o código fonte
COPY engine/ /app/engine/
COPY config/ /app/config/
COPY docker/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV WA_HEADLESS=true

# Diretórios de dados persistentes montados via volume
VOLUME ["/app/data", "/app/config"]

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--scheduler"]
