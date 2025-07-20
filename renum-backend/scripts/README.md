# Scripts para Gerenciamento do Banco de Dados Supabase

Este diretório contém scripts para gerenciar o esquema do banco de dados Supabase para o projeto Renum.

## Arquivos SQL

- `create_agent_share_table.sql` - Cria a tabela `agent_shares` e configura políticas RLS para compartilhamento de agentes
- `agent_share_rls_policies.sql` - Contém apenas as políticas RLS para a tabela `agent_shares` (incluído no arquivo anterior)

## Scripts de Aplicação

- `apply_supabase_schema.py` - Script Python para aplicar o esquema no Supabase
- `apply_schema.bat` - Script batch para Windows que executa o script Python

## Como Usar

### Pré-requisitos

- Python 3.6 ou superior
- Credenciais do Supabase (URL e chave de serviço)
- Arquivo `.env` na raiz do projeto com as credenciais do Supabase

### Aplicar o Esquema

1. Certifique-se de que o arquivo `.env` na raiz do projeto contém as seguintes variáveis:
   ```
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_SERVICE_KEY=sua-chave-de-servico
   ```

2. Execute o script batch:
   ```
   cd renum-backend
   scripts\apply_schema.bat
   ```

3. O script irá:
   - Verificar se o Python está instalado
   - Instalar dependências necessárias
   - Verificar se o arquivo SQL existe
   - Verificar se o arquivo `.env` existe
   - Executar o script Python para aplicar o esquema

### Executar Manualmente

Se preferir, você pode executar o script Python diretamente:

```
cd renum-backend
python scripts\apply_supabase_schema.py scripts\create_agent_share_table.sql
```

## Solução de Problemas

### Erro de Conexão

Se você encontrar erros de conexão, verifique:
- Se as credenciais do Supabase estão corretas
- Se o projeto Supabase está acessível
- Se a chave de serviço tem permissões suficientes

### Erro de SQL

Se você encontrar erros de SQL, verifique:
- Se a tabela `agents` já existe
- Se a tabela `clients` já existe
- Se a extensão `uuid-ossp` está habilitada

### Outros Erros

Para outros erros, verifique os logs do script para obter mais detalhes.