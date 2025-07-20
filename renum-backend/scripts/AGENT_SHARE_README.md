# Implementação do Compartilhamento de Agentes

Este documento descreve como aplicar o esquema de compartilhamento de agentes no Supabase e implementar a funcionalidade no sistema Renum.

## Visão Geral

O sistema de compartilhamento de agentes permite que usuários compartilhem seus agentes com outros usuários, definindo diferentes níveis de permissão:

- **View (Visualizar)**: Permite apenas visualizar o agente e suas configurações
- **Use (Utilizar)**: Permite visualizar e usar o agente (conversar)
- **Edit (Editar)**: Permite visualizar, usar e editar o agente
- **Admin (Administrar)**: Permite visualizar, usar, editar e compartilhar o agente

## Arquivos Implementados

### Backend

1. **Modelo de Dados**
   - `app/models/agent_share.py`: Define o modelo `AgentShare` e os níveis de permissão

2. **Repositório**
   - `app/repositories/agent_share.py`: Implementa o repositório `AgentShareRepository`

3. **API Endpoints**
   - `app/api/routes/agent_share.py`: Define os endpoints para gerenciar compartilhamentos
   - `app/api/schemas/agent_share.py`: Define os schemas para validação de dados

4. **Scripts SQL**
   - `scripts/create_agent_share_table.sql`: Script para criar a tabela e políticas RLS
   - `scripts/agent_share_rls_policies.sql`: Políticas RLS para controle de acesso

### Frontend

1. **Componentes**
   - `src/components/ShareAgentModal.tsx`: Modal para compartilhar agentes
   - Atualização de `src/components/AgentCard.tsx`: Indicadores de compartilhamento

2. **Hooks**
   - `src/hooks/useAgentSharing.ts`: Hook para gerenciar compartilhamentos

3. **Páginas**
   - Atualização de `src/pages/agents/[id]/index.tsx`: Botão de compartilhamento
   - Atualização de `src/pages/dashboard.tsx`: Seção de agentes compartilhados

## Como Aplicar o Esquema no Supabase

### Pré-requisitos

1. Certifique-se de que o arquivo `.env` na raiz do projeto `renum-backend` contém as seguintes variáveis:
   ```
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-anonima
   SUPABASE_SERVICE_KEY=sua-chave-de-servico
   ```

2. Certifique-se de que as tabelas `agents` e `clients` já existem no Supabase.

### Aplicar o Esquema

#### Usando o Script Batch (Windows)

1. Abra um terminal na raiz do projeto `renum-backend`
2. Execute o script batch:
   ```
   scripts\apply_agent_share_schema.bat
   ```

#### Usando o Script Python Diretamente

1. Abra um terminal na raiz do projeto `renum-backend`
2. Execute o script Python:
   ```
   python scripts\apply_agent_share_schema.py scripts\create_agent_share_table.sql
   ```

### Verificar a Aplicação do Esquema

1. Acesse o painel do Supabase
2. Vá para a seção "Table Editor"
3. Verifique se a tabela `agent_shares` foi criada
4. Vá para a seção "Authentication" > "Policies"
5. Verifique se as políticas RLS foram aplicadas à tabela `agent_shares`

## Como Testar a Funcionalidade

### Backend

1. Certifique-se de que o backend está em execução:
   ```
   cd renum-backend
   uvicorn app.main:app --reload
   ```

2. Teste os endpoints usando um cliente HTTP como o Postman ou curl:
   - `POST /api/v2/agents/{agent_id}/share`: Compartilhar agente
   - `GET /api/v2/agents/{agent_id}/shares`: Listar compartilhamentos
   - `DELETE /api/v2/agents/{agent_id}/shares/{share_id}`: Remover compartilhamento
   - `PUT /api/v2/agents/{agent_id}/shares/{share_id}`: Atualizar permissões
   - `GET /api/v2/agents/shared-with-me`: Listar agentes compartilhados com o usuário

### Frontend

1. Certifique-se de que o frontend está em execução:
   ```
   cd renum-frontend
   npm run dev
   ```

2. Acesse a aplicação no navegador
3. Vá para a página de detalhes de um agente
4. Clique no botão "Compartilhar"
5. Teste o compartilhamento com outro usuário
6. Verifique se o agente aparece na seção "Compartilhados Comigo" do outro usuário

## Solução de Problemas

### Erro ao Aplicar o Esquema

Se você encontrar erros ao aplicar o esquema, verifique:

1. Se as credenciais do Supabase estão corretas no arquivo `.env`
2. Se as tabelas `agents` e `clients` já existem no Supabase
3. Se a extensão `uuid-ossp` está habilitada no Supabase

### Erro ao Usar a Funcionalidade

Se você encontrar erros ao usar a funcionalidade, verifique:

1. Se o esquema foi aplicado corretamente
2. Se as políticas RLS estão funcionando corretamente
3. Se os endpoints da API estão respondendo corretamente

## Próximos Passos

1. Implementar notificações para usuários quando um agente é compartilhado com eles
2. Adicionar suporte para compartilhamento em lote (múltiplos agentes)
3. Implementar compartilhamento com grupos de usuários
4. Adicionar métricas de uso por usuário compartilhado