# Plano de Implementação Renum

Este documento detalha o plano de implementação para as funcionalidades pendentes da plataforma Renum, conforme solicitado.

## 1. Compartilhamento de Agentes

### 1.1 Modelo de Dados para Compartilhamento

#### Backend
- Criar modelo `AgentShare` em `app/models/agent_share.py`
  - Campos: id, agent_id, owner_id, user_id, permission_level, created_at, updated_at
  - Permission levels: "view", "edit", "admin"
- Implementar repositório `AgentShareRepository` em `app/repositories/agent_share.py`
  - Métodos CRUD básicos
  - Métodos para verificação de permissões

#### Banco de Dados
- Criar tabela `agent_shares` no Supabase
- Implementar políticas RLS para controle de acesso
  - Política para criadores de agentes
  - Política para usuários com compartilhamento

### 1.2 Endpoints de API para Controle de Permissões

#### Backend
- Criar rotas em `app/api/routes/agent_share.py`:
  - `POST /api/v2/agents/{agent_id}/share` - Compartilhar agente
  - `GET /api/v2/agents/{agent_id}/shares` - Listar compartilhamentos
  - `DELETE /api/v2/agents/{agent_id}/shares/{share_id}` - Remover compartilhamento
  - `PUT /api/v2/agents/{agent_id}/shares/{share_id}` - Atualizar permissões
- Criar schemas em `app/api/schemas/agent_share.py`:
  - `AgentShareCreate`
  - `AgentShareResponse`
  - `AgentShareUpdate`
- Atualizar rota `GET /api/v2/agents` para incluir agentes compartilhados

### 1.3 Interface de Usuário para Compartilhamento

#### Frontend
- Criar componente `ShareAgentModal.tsx` em `src/components`
  - Campo de busca de usuários
  - Seletor de nível de permissão
  - Lista de compartilhamentos existentes
- Atualizar página de detalhes do agente para incluir botão de compartilhamento
- Implementar hook `useAgentSharing` em `src/hooks`
  - Métodos para compartilhar, listar e remover compartilhamentos
- Atualizar listagem de agentes para exibir indicador de agentes compartilhados

### 1.4 Políticas RLS no Supabase

#### SQL
- Criar script SQL para políticas RLS:
  ```sql
  -- Política para criadores de agentes
  CREATE POLICY "Criadores podem gerenciar seus agentes"
  ON public.agents
  FOR ALL
  USING (auth.uid() = user_id);
  
  -- Política para usuários com compartilhamento
  CREATE POLICY "Usuários com compartilhamento podem acessar agentes"
  ON public.agents
  FOR SELECT
  USING (
    auth.uid() IN (
      SELECT user_id FROM public.agent_shares
      WHERE agent_id = id
    )
  );
  
  -- Política para edição baseada em permissões
  CREATE POLICY "Usuários com permissão de edição podem atualizar agentes"
  ON public.agents
  FOR UPDATE
  USING (
    auth.uid() IN (
      SELECT user_id FROM public.agent_shares
      WHERE agent_id = id AND permission_level IN ('edit', 'admin')
    )
  );
  ```

## 2. Interface de Gerenciamento do Módulo RAG

### 2.1 Upload de Documentos e Links

#### Backend
- Atualizar endpoints em `app/rag/api_document.py`:
  - Melhorar suporte para upload de múltiplos arquivos
  - Adicionar suporte para crawling de links
- Implementar processador de links em `app/rag/services/link_processor.py`
  - Extração de conteúdo de páginas web
  - Conversão para formato compatível com RAG

#### Frontend
- Criar componente `DocumentUploader.tsx` em `src/components/rag`
  - Suporte para drag-and-drop
  - Visualização de progresso
  - Validação de tipos de arquivo
- Criar componente `LinkCrawler.tsx` em `src/components/rag`
  - Campo para inserção de URLs
  - Opções de profundidade de crawling
  - Visualização de progresso

### 2.2 Interface Visual de Gerenciamento

#### Frontend
- Criar página `src/pages/knowledge-bases/[id]/index.tsx`
  - Visão geral da base de conhecimento
  - Estatísticas (documentos, tokens, etc.)
- Criar página `src/pages/knowledge-bases/[id]/documents.tsx`
  - Listagem de documentos com filtros
  - Ações em lote (excluir, mover)
- Implementar hook `useKnowledgeBase` em `src/hooks`
  - Métodos para gerenciar bases de conhecimento

### 2.3 Visualização de Documentos e Fragments

#### Frontend
- Criar componente `DocumentViewer.tsx` em `src/components/rag`
  - Visualização do conteúdo do documento
  - Highlighting de texto
- Criar componente `FragmentViewer.tsx` em `src/components/rag`
  - Visualização dos fragments gerados
  - Metadados de embedding
- Implementar página `src/pages/knowledge-bases/[id]/documents/[documentId].tsx`
  - Detalhes do documento
  - Lista de fragments

## 3. Sistema de Rastreamento e Limites

### 3.1 Controle de Uso por Plano

#### Backend
- Criar modelo `Plan` em `app/models/plan.py`
  - Campos: id, name, description, limits (JSON)
- Criar modelo `UserPlan` em `app/models/user_plan.py`
  - Campos: id, user_id, plan_id, start_date, end_date
- Implementar serviço `LimitService` em `app/services/limit_service.py`
  - Verificação de limites
  - Contabilização de uso

#### Banco de Dados
- Criar tabelas `plans` e `user_plans` no Supabase
- Implementar triggers para atualização automática de contadores

### 3.2 Modelo de Faturamento

#### Backend
- Criar modelo `Usage` em `app/models/usage.py`
  - Campos: id, user_id, resource_type, resource_id, quantity, timestamp
- Implementar serviço `BillingService` em `app/services/billing_service.py`
  - Cálculo de uso por período
  - Geração de relatórios

#### Frontend
- Criar página `src/pages/billing/index.tsx`
  - Resumo de uso
  - Histórico de faturamento
- Criar componente `UsageChart.tsx` em `src/components/billing`
  - Gráficos de uso por recurso
  - Filtros por período

### 3.3 Coleta de Dados de Uso

#### Backend
- Implementar middleware `UsageTrackingMiddleware` em `app/api/middlewares/usage_tracking.py`
  - Interceptação de requisições para endpoints-chave
  - Registro de uso
- Atualizar endpoints principais para registrar uso:
  - Chamadas de agentes
  - Uploads de documentos
  - Criação de embeddings

### 3.4 Relatório de Consumo

#### Backend
- Criar endpoints em `app/api/routes/usage.py`:
  - `GET /api/v2/usage` - Resumo de uso
  - `GET /api/v2/usage/details` - Detalhes por recurso
  - `GET /api/v2/usage/export` - Exportação de relatório

#### Frontend
- Criar página `src/pages/reports/usage.tsx`
  - Filtros por período e recurso
  - Tabelas e gráficos de uso
  - Opção de exportação

## 4. Armazenamento de Arquivos (Supabase Storage)

### 4.1 Integração com Supabase Storage

#### Backend
- Implementar serviço `StorageService` em `app/services/storage_service.py`
  - Upload de arquivos
  - Download de arquivos
  - Gerenciamento de permissões
- Criar endpoints em `app/api/routes/storage.py`:
  - `POST /api/v2/storage/upload` - Upload de arquivo
  - `GET /api/v2/storage/download/{file_id}` - Download de arquivo
  - `DELETE /api/v2/storage/files/{file_id}` - Exclusão de arquivo

#### Frontend
- Criar hook `useStorage` em `src/hooks`
  - Métodos para upload, download e gerenciamento de arquivos
- Implementar componente `FileUploader.tsx` em `src/components/storage`
  - Interface de upload com progresso
  - Validação de tipos e tamanhos

### 4.2 Versionamento de Arquivos

#### Backend
- Criar modelo `FileVersion` em `app/models/file_version.py`
  - Campos: id, file_id, version, path, size, created_at, created_by
- Implementar lógica de versionamento em `StorageService`
  - Criação de novas versões
  - Recuperação de versões anteriores

#### Frontend
- Criar componente `FileVersionHistory.tsx` em `src/components/storage`
  - Listagem de versões
  - Comparação entre versões
  - Restauração de versões anteriores

### 4.3 Organização Hierárquica

#### Backend
- Criar modelo `Folder` em `app/models/folder.py`
  - Campos: id, name, parent_id, user_id, created_at
- Implementar endpoints em `app/api/routes/storage.py`:
  - `POST /api/v2/storage/folders` - Criar pasta
  - `GET /api/v2/storage/folders/{folder_id}` - Listar conteúdo
  - `PUT /api/v2/storage/folders/{folder_id}` - Atualizar pasta
  - `DELETE /api/v2/storage/folders/{folder_id}` - Excluir pasta

#### Frontend
- Criar componente `FolderExplorer.tsx` em `src/components/storage`
  - Navegação em árvore de pastas
  - Operações de arrastar e soltar
  - Ações contextuais (renomear, excluir)

## 5. Sistema de Auditoria

### 5.1 Log de Ações Sensíveis

#### Backend
- Criar modelo `AuditLog` em `app/models/audit_log.py`
  - Campos: id, user_id, action, resource_type, resource_id, details, ip_address, timestamp
- Implementar serviço `AuditService` em `app/services/audit_service.py`
  - Registro de ações
  - Consulta de logs

#### Banco de Dados
- Criar tabela `audit_logs` no Supabase
- Implementar políticas RLS para acesso restrito

### 5.2 Trilhas de Auditoria

#### Backend
- Criar endpoints em `app/api/routes/audit.py`:
  - `GET /api/v2/audit/logs` - Listar logs de auditoria
  - `GET /api/v2/audit/logs/{log_id}` - Detalhes do log
- Implementar filtros e paginação para consulta eficiente

#### Frontend
- Criar página `src/pages/admin/audit.tsx`
  - Filtros por usuário, ação e período
  - Visualização detalhada de logs
  - Exportação de relatórios

### 5.3 Registros no Backend

#### Backend
- Atualizar endpoints sensíveis para registrar ações:
  - Criação e edição de agentes
  - Gerenciamento de credenciais
  - Compartilhamento de recursos
  - Alterações em bases de conhecimento
- Implementar middleware `AuditMiddleware` em `app/api/middlewares/audit.py`
  - Captura automática de informações de contexto
  - Registro de tentativas de acesso não autorizado

## 6. Otimizações no Frontend

### 6.1 Performance e Carregamento

#### Frontend
- Implementar lazy loading para componentes pesados
  - Usar `dynamic` do Next.js para importação dinâmica
- Otimizar renderização de listas grandes
  - Implementar virtualização com `react-window` ou similar
- Melhorar estratégia de caching
  - Configurar `staleTime` e `cacheTime` no React Query
  - Implementar prefetching para navegação comum

### 6.2 Ajustes Visuais e Acessibilidade

#### Frontend
- Melhorar contraste de cores para acessibilidade
  - Verificar conformidade com WCAG 2.1 AA
- Adicionar atributos ARIA apropriados
  - Labels, roles e descrições
- Implementar navegação por teclado
  - Focus management
  - Keyboard shortcuts

### 6.3 Padronização de UI

#### Frontend
- Criar ou atualizar `src/components/ui/ThemeProvider.tsx`
  - Configuração centralizada de tema
  - Suporte para modo escuro
- Refatorar componentes para usar design system consistente
  - Espaçamento, tipografia e cores padronizados
- Criar documentação de componentes
  - Exemplos de uso
  - Props disponíveis

## Cronograma Estimado

1. **Compartilhamento de Agentes**: 1 semana
2. **Interface de Gerenciamento do Módulo RAG**: 1-2 semanas
3. **Sistema de Rastreamento e Limites**: 1-2 semanas
4. **Armazenamento de Arquivos**: 1 semana
5. **Sistema de Auditoria**: 1 semana
6. **Otimizações no Frontend**: 1-2 semanas

Total estimado: 6-9 semanas

## Priorização Sugerida

1. Compartilhamento de Agentes
2. Interface de Gerenciamento do Módulo RAG
3. Otimizações no Frontend
4. Sistema de Rastreamento e Limites
5. Armazenamento de Arquivos
6. Sistema de Auditoria

Esta priorização foca primeiro nas funcionalidades que agregam valor imediato aos usuários, seguidas por melhorias de experiência e, por fim, recursos administrativos e de infraestrutura.