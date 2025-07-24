FROM python:3.11-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Expõe a porta
EXPOSE 9000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]