# Implementation Plan

## Correção Sistemática dos Erros TypeScript Restantes (79 erros)

Após a conclusão da migração React Query v5, restam 79 erros TypeScript que precisam ser corrigidos sistematicamente.

- [x] 1. Corrigir Hooks WebSocket e Tipos de Notificação


  - Corrigir propriedades faltantes em WebSocketNotification (metadata, status)
  - Atualizar useWebSocketNotifications para incluir deleteNotification e userId
  - Corrigir propriedades faltantes em useExecutionMonitor (executionData, isMonitoring, startMonitoring, stopMonitoring)
  - Resolver problemas de declaração de variáveis antes do uso (syncWithServer, markAsRead)
  - _Requirements: 1.1, 1.2, 1.3, 1.4_



- [x] 2. Corrigir Tipagem do Agent e Propriedades Faltantes


  - Adicionar propriedades knowledge_bases e usage ao tipo Agent
  - Corrigir erros em pages/agents/[id]/index.tsx relacionados a essas propriedades


  - Garantir compatibilidade entre diferentes definições de Agent
  - _Requirements: 2.1, 2.2, 2.3_


- [x] 3. Resolver Problemas de Declaração de Variáveis em Hooks

  - Corrigir erros TS2448/TS2454 (variável usada antes da declaração)
  - Resolver loadPreferences em NotificationSettings.tsx
  - Resolver loadStatistics em useExecutionErrors.ts
  - Resolver fetchAgentDetails e fetchAgents em páginas
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Corrigir Erros de Importação e Exportação


  - Resolver problema com RealTimeTeamExecutionsProps export
  - Instalar ou remover dependência react-beautiful-dnd
  - Corrigir conflito de exportação useExecutionMonitor
  - Resolver importações quebradas (team-execution-hooks, lib/supabase)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Configurar Testes Jest e @testing-library/jest-dom



  - Instalar e configurar @testing-library/jest-dom
  - Corrigir erros toBeInTheDocument, toHaveClass, toBeDisabled
  - Configurar setup de testes adequadamente
  - _Requirements: 5.1, 5.2_

- [x] 6. Corrigir Componentes UI e Tipos


  - Adicionar variant="destructive" ao componente Button
  - Adicionar propriedade token ao tipo User
  - Corrigir propriedades duplicadas em WebSocket components (TS2783)
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 7. Resolver Problemas de AgentRole e Indexação


  - Corrigir problemas de AgentRole undefined em ExecutionOrderPreview
  - Resolver problemas de indexação em workflow-utils.ts
  - Garantir que AgentRole seja sempre definido
  - _Requirements: 7.1, 7.2_

- [x] 8. Corrigir Problemas Específicos de Componentes


  - Resolver erro de ExecutionProgress props em RealTimeExecutionProgress
  - Corrigir problema de indexação em pages/teams/new.tsx
  - Resolver problema de useRouter em test-utils.tsx
  - Corrigir parâmetros any implícitos em TeamMembersEditor
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 9. Validação Final e Testes de Compilação


  - Executar npx tsc --noEmit após cada conjunto de correções
  - Documentar progresso de redução de erros
  - Garantir que não há regressões
  - Validar build completo do projeto
  - _Requirements: 9.1, 9.2_

- [x] 10. Documentação e Limpeza Final


  - Documentar todas as correções realizadas
  - Criar guia de prevenção de erros similares
  - Atualizar configurações de linting se necessário
  - Criar resumo final das correções
  - _Requirements: 10.1, 10.2_