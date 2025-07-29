FROM python:3.11-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Expõe a porta
EXPOSE 9000

# Instala gunicorn para multi-worker setup
RUN pip install --no-cache-dir gunicorn

# Configuração de workers otimizada para produção
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV TIMEOUT=120
ENV KEEPALIVE=2
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=100

# Copy gunicorn configuration
COPY gunicorn.conf.py .

# Comando para iniciar a aplicação com multi-workers
CMD ["gunicorn", "app.main:app", "--config", "gunicorn.conf.py", "--bind", "0.0.0.0:9000"]