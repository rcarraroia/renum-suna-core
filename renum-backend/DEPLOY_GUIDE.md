# Guia de Deploy do Backend Renum na VPS

Este guia descreve o processo de deploy do Backend Renum na mesma VPS onde o Backend Suna já está instalado.

> **IMPORTANTE**: O Backend Renum utiliza o prefixo `renum_` para todas as suas tabelas no banco de dados Supabase, para distingui-las das tabelas do sistema Suna. Isso garante compatibilidade e facilita a manutenção.

## Pré-requisitos

- Acesso SSH à VPS (IP: 157.180.39.41)
- Python 3.11+ instalado na VPS
- Pip e virtualenv instalados na VPS
- Arquivo `renum-backend-deploy.zip` preparado com o script `prepare_deploy.bat`

## Etapas de Deploy

### 1. Preparar o Pacote de Deploy

1. Execute o script `prepare_deploy.bat` no ambiente de desenvolvimento:
   ```
   prepare_deploy.bat
   ```

2. Isso criará um arquivo `renum-backend-deploy.zip` com todos os arquivos necessários para o deploy.

### 2. Transferir o Pacote para a VPS

1. Use SCP para transferir o arquivo para a VPS:
   ```
   scp renum-backend-deploy.zip usuario@157.180.39.41:/home/usuario/
   ```

### 3. Configurar o Ambiente na VPS

1. Conecte-se à VPS via SSH:
   ```
   ssh usuario@157.180.39.41
   ```

2. Crie um diretório para o Backend Renum:
   ```
   mkdir -p /opt/renum-backend
   ```

3. Extraia o pacote de deploy:
   ```
   unzip renum-backend-deploy.zip -d /opt/renum-backend
   cd /opt/renum-backend
   ```

4. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

5. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

6. Configure as variáveis de ambiente:
   ```
   cp .env.example .env
   nano .env
   ```
   
   Edite o arquivo `.env` com as configurações corretas para o ambiente de produção.

### 4. Configurar o Serviço Systemd

1. Crie um arquivo de serviço systemd:
   ```
   sudo nano /etc/systemd/system/renum-backend.service
   ```

2. Adicione o seguinte conteúdo:
   ```
   [Unit]
   Description=Renum Backend Service
   After=network.target

   [Service]
   User=usuario
   Group=usuario
   WorkingDirectory=/opt/renum-backend
   Environment="PATH=/opt/renum-backend/venv/bin"
   ExecStart=/opt/renum-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Habilite e inicie o serviço:
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable renum-backend
   sudo systemctl start renum-backend
   ```

4. Verifique o status do serviço:
   ```
   sudo systemctl status renum-backend
   ```

### 5. Configurar Nginx como Proxy Reverso

1. Instale o Nginx se ainda não estiver instalado:
   ```
   sudo apt update
   sudo apt install nginx
   ```

2. Crie um arquivo de configuração para o Renum Backend:
   ```
   sudo nano /etc/nginx/sites-available/renum-backend
   ```

3. Adicione o seguinte conteúdo:
   ```
   server {
       listen 80;
       server_name api.renum.com.br; # Substitua pelo domínio real

       location / {
           proxy_pass http://localhost:9000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. Crie um link simbólico para habilitar o site:
   ```
   sudo ln -s /etc/nginx/sites-available/renum-backend /etc/nginx/sites-enabled/
   ```

5. Teste a configuração do Nginx:
   ```
   sudo nginx -t
   ```

6. Reinicie o Nginx:
   ```
   sudo systemctl restart nginx
   ```

### 6. Configurar SSL com Certbot (Opcional)

1. Instale o Certbot:
   ```
   sudo apt install certbot python3-certbot-nginx
   ```

2. Obtenha um certificado SSL:
   ```
   sudo certbot --nginx -d api.renum.com.br
   ```

3. Siga as instruções do Certbot para configurar o SSL.

### 7. Verificar a Instalação

1. Teste o acesso à API:
   ```
   curl http://localhost:9000/health
   ```

2. Verifique os logs do serviço:
   ```
   sudo journalctl -u renum-backend -f
   ```

## Solução de Problemas

### Problema: O serviço não inicia

1. Verifique os logs:
   ```
   sudo journalctl -u renum-backend -f
   ```

2. Verifique se todas as variáveis de ambiente estão configuradas corretamente no arquivo `.env`.

3. Verifique se todas as dependências foram instaladas corretamente:
   ```
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Problema: Erro de conexão com o Supabase

1. Verifique se as credenciais do Supabase estão corretas no arquivo `.env`.

2. Verifique se a VPS tem acesso à internet e pode se conectar ao Supabase.

3. Teste a conexão com o Supabase:
   ```
   python -c "from app.core.supabase_client import get_supabase_client; print(get_supabase_client().table('users').select('*').limit(1).execute())"
   ```

### Problema: Conflito de porta

1. Verifique se a porta 9000 já está em uso:
   ```
   sudo netstat -tulpn | grep 9000
   ```

2. Se a porta estiver em uso, altere a porta no arquivo de serviço systemd e reinicie o serviço.

## Manutenção

### Atualizar o Backend

1. Prepare um novo pacote de deploy seguindo as etapas da seção "Preparar o Pacote de Deploy".

2. Transfira o novo pacote para a VPS.

3. Faça backup da configuração atual:
   ```
   cp /opt/renum-backend/.env /opt/renum-backend/.env.backup
   ```

4. Pare o serviço:
   ```
   sudo systemctl stop renum-backend
   ```

5. Extraia o novo pacote:
   ```
   rm -rf /opt/renum-backend/*
   unzip renum-backend-deploy.zip -d /opt/renum-backend
   ```

6. Restaure a configuração:
   ```
   cp /opt/renum-backend/.env.backup /opt/renum-backend/.env
   ```

7. Atualize as dependências:
   ```
   cd /opt/renum-backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

8. Inicie o serviço:
   ```
   sudo systemctl start renum-backend
   ```

### Monitoramento

1. Monitore os logs do serviço:
   ```
   sudo journalctl -u renum-backend -f
   ```

2. Verifique o status do serviço:
   ```
   sudo systemctl status renum-backend
   ```

3. Monitore o uso de recursos:
   ```
   top
   htop
   ```

---

Este guia foi criado em 19/07/2025 e pode precisar de atualizações conforme o projeto evolui.