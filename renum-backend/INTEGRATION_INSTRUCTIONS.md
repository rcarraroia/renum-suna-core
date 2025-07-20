# Instruções de Integração Renum-Suna

Este documento fornece instruções detalhadas para integrar o backend Renum com o sistema Suna na VPS.

## Pré-requisitos

- Acesso SSH à VPS
- Sistema Suna já instalado e funcionando na VPS
- Credenciais do Supabase (URL, chave anônima e chave de serviço)
- Python 3.8+ instalado na VPS

## Etapas de Integração

### 1. Preparar os Arquivos para Deploy

1. Clone o repositório do backend Renum:
   ```bash
   git clone https://github.com/seu-usuario/renum-backend.git
   cd renum-backend
   ```

2. Certifique-se de que o arquivo `.env` está configurado corretamente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com as credenciais corretas
   ```

3. Verifique se o script `create_renum_tables.sql` contém todas as tabelas necessárias com o prefixo `renum_`.

### 2. Executar o Script de Integração na VPS

1. Transfira os arquivos para a VPS:
   ```bash
   scp -r renum-backend/ usuario@ip-da-vps:/tmp/
   ```

2. Conecte-se à VPS via SSH:
   ```bash
   ssh usuario@ip-da-vps
   ```

3. Execute o script de integração:
   ```bash
   cd /tmp/renum-backend
   chmod +x scripts/setup_vps_integration.sh
   sudo ./scripts/setup_vps_integration.sh /tmp/renum-backend
   ```

4. O script irá:
   - Fazer backup do sistema existente
   - Criar diretório para o backend Renum
   - Copiar os arquivos para o diretório
   - Configurar ambiente virtual Python
   - Aplicar o esquema do banco de dados
   - Configurar serviço systemd
   - Configurar Nginx como proxy reverso

### 3. Aplicar o Esquema do Banco de Dados

1. Certifique-se de que o arquivo `.env` contém as credenciais corretas do Supabase.

2. Execute o script para aplicar o esquema:
   ```bash
   cd /opt/renum-backend
   python scripts/execute_sql_direct.py scripts/create_renum_tables.sql
   ```

3. Verifique se as tabelas foram criadas corretamente:
   ```bash
   python scripts/verify_integration.py
   ```

### 4. Configurar o NGINX

1. Copie o arquivo de configuração do NGINX:
   ```bash
   sudo cp /opt/renum-backend/scripts/nginx-renum.conf /etc/nginx/sites-available/renum-backend
   ```

2. Crie um link simbólico:
   ```bash
   sudo ln -s /etc/nginx/sites-available/renum-backend /etc/nginx/sites-enabled/
   ```

3. Teste a configuração do NGINX:
   ```bash
   sudo nginx -t
   ```

4. Reinicie o NGINX:
   ```bash
   sudo systemctl restart nginx
   ```

### 5. Verificar a Integração

1. Execute o script de verificação:
   ```bash
   cd /opt/renum-backend
   python scripts/verify_integration.py
   ```

2. Verifique se:
   - A conexão com o Supabase está funcionando
   - As tabelas com prefixo `renum_` foram criadas
   - A comunicação com o backend Suna está funcionando
   - A configuração do NGINX está correta

3. Teste os endpoints da API:
   ```bash
   curl http://localhost:9000/health
   ```

### 6. Atualizar o Frontend Renum

1. Atualize o arquivo de configuração do frontend para apontar para a API:
   ```
   NEXT_PUBLIC_API_URL=https://api.renum.com.br
   ```

2. Implante o frontend no Vercel.

## Solução de Problemas

### Problema: Erro ao conectar com o Supabase

1. Verifique se as credenciais no arquivo `.env` estão corretas.
2. Verifique se a VPS tem acesso à internet.
3. Teste a conexão manualmente:
   ```python
   import os
   from dotenv import load_dotenv
   from supabase import create_client

   load_dotenv()
   supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
   result = supabase.table("agents").select("*").limit(1).execute()
   print(result)
   ```

### Problema: Erro ao aplicar o esquema do banco de dados

1. Verifique se o script SQL está correto.
2. Tente executar o script manualmente no SQL Editor do Supabase.
3. Verifique se há erros de sintaxe no script.

### Problema: Erro ao comunicar com o backend Suna

1. Verifique se o backend Suna está em execução:
   ```bash
   systemctl status suna
   ```

2. Verifique se a URL do Suna no arquivo `.env` está correta.
3. Teste a conexão manualmente:
   ```bash
   curl http://localhost:8000/health
   ```

### Problema: Erro na configuração do NGINX

1. Verifique a sintaxe da configuração:
   ```bash
   sudo nginx -t
   ```

2. Verifique os logs do NGINX:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Certifique-se de que as portas 8000 e 9000 estão sendo usadas pelos backends:
   ```bash
   sudo netstat -tulpn | grep -E '8000|9000'
   ```

## Próximos Passos

Após a integração bem-sucedida, você pode:

1. Desenvolver o painel administrativo
2. Implementar funcionalidades adicionais
3. Configurar monitoramento e alertas
4. Configurar backup automático