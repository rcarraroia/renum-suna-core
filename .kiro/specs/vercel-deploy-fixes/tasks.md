# Implementation Plan - Correção de Erros de Deploy no Vercel

## Fase 1: Correções Críticas de Importação

- [x] 1. Corrigir erro de importação apiClient em ShareAgentModal.tsx


  - Verificar se apiClient existe em ../lib/api-client ou ../services/api-client
  - Ajustar importação para usar exportação correta (nomeada vs default)
  - Testar se componente funciona após correção
  - _Requirements: 1.1, 1.5_


- [x] 2. Corrigir erro de propriedade showToast em ShareAgentModal.tsx


  - Examinar hook useToast() para identificar métodos disponíveis
  - Substituir showToast por método correto (success, error, addToast)
  - Verificar se funcionalidade de toast continua funcionando


  - _Requirements: 1.2, 1.5_

- [x] 3. Corrigir erro de importação Tool do lucide-react em ToolSelector.tsx


  - Verificar ícones disponíveis no lucide-react


  - Substituir Tool por Wrench, Settings ou outro ícone apropriado
  - Usar alias na importação: import { Wrench as Tool }
  - _Requirements: 1.3, 1.5_

- [x] 4. Corrigir erro de importação ToolCall em ToolUsageDisplay.tsx


  - Verificar como ToolCall é exportado em ChatInterface.tsx


  - Ajustar importação para type import se necessário
  - Corrigir sintaxe de importação (nomeada vs default)
  - _Requirements: 1.4, 1.5_


## Fase 2: Correções de React Hooks Dependencies


- [x] 5. Corrigir dependências em NotificationSettings.tsx

  - Adicionar 'loadPreferences' ao array de dependências do useEffect (linha 50)
  - Verificar se não causa loop infinito
  - Testar funcionalidade de carregamento de preferências
  - _Requirements: 2.1, 2.4_

- [x] 6. Corrigir dependências em WorkflowConfigurator.tsx

  - Adicionar 'createDefaultAgent', 'onChange', 'value' ao useEffect (linha 53)
  - Considerar useCallback para onChange se necessário
  - Validar que workflow configurator funciona corretamente
  - _Requirements: 2.1, 2.2, 2.4_


- [x] 7. Corrigir dependências em componentes WebSocket

  - ConnectionLostBanner.tsx: adicionar 'timer' ao useEffect (linha 52)
  - ConnectionLostOverlay.tsx: adicionar 'disconnectedTime', 'timer' (linha 62)
  - ReconnectionProgress.tsx: adicionar 'visible' ao useEffect (linha 68)
  - Testar reconexão WebSocket após mudanças
  - _Requirements: 2.1, 2.4_

- [x] 8. Corrigir dependências em WebSocketContext.tsx


  - Adicionar 'publish', 'subscribe' ao useMemo (linha 96)
  - Verificar se context providers funcionam corretamente
  - Testar comunicação WebSocket
  - _Requirements: 2.3, 2.4_

- [x] 9. Corrigir dependências em hooks customizados


  - useExecutions.ts: adicionar 'polling' ao useEffect (linha 82)
  - useWebSocket.ts: adicionar 'options' ao useEffect (linha 67)
  - useWebSocketNotifications.ts: adicionar 'syncWithServer', 'markAsRead'
  - useExecutionErrors.ts: adicionar 'loadStatistics' ao useCallback (linha 197)
  - Testar cada hook individualmente
  - _Requirements: 2.1, 2.2, 2.4_

- [x] 10. Corrigir dependências em páginas


  - pages/agents/[id]/index.tsx: adicionar 'fetchAgentDetails' (linha 39)
  - pages/dashboard.tsx: adicionar 'fetchAgents' (linha 20)
  - Verificar se páginas carregam dados corretamente
  - _Requirements: 2.1, 2.4_

- [x] 11. Remover dependência desnecessária em useRealTimeExecutions.ts


  - Remover 'handleExecutionUpdate' do useCallback (linha 169)
  - Verificar se execuções em tempo real continuam funcionando
  - _Requirements: 2.2, 2.4_

## Fase 3: Atualização de Dependências Deprecated

- [x] 12. Atualizar rimraf para versão 4+


  - Executar: npm install rimraf@^4.0.0
  - Verificar se scripts que usam rimraf continuam funcionando
  - Ajustar sintaxe se necessário (rimraf v4 tem API diferente)
  - _Requirements: 3.2_


- [x] 13. Atualizar glob para versão 9+

  - Executar: npm install glob@^9.0.0
  - Verificar compatibilidade com ferramentas que usam glob
  - Ajustar código se necessário (glob v9 é async por padrão)
  - _Requirements: 3.4_

- [x] 14. Atualizar ESLint para versão suportada


  - Executar: npm install eslint@^9.0.0
  - Atualizar configuração ESLint se necessário
  - Verificar se regras customizadas ainda funcionam
  - _Requirements: 3.3_

- [x] 15. Substituir pacotes @humanwhocodes deprecated


  - Executar: npm uninstall @humanwhocodes/object-schema @humanwhocodes/config-array
  - Executar: npm install @eslint/object-schema @eslint/config-array
  - Verificar se ESLint continua funcionando
  - _Requirements: 3.3_

- [x] 16. Remover ou substituir outros pacotes deprecated


  - Avaliar inflight: considerar lru-cache como alternativa
  - Avaliar domexception: usar DOMException nativo
  - Avaliar abab: usar atob()/btoa() nativos
  - Testar funcionalidade após mudanças
  - _Requirements: 3.1, 3.5_

## Fase 4: Validação e Testes

- [x] 17. Implementar script de validação de build local


  - Criar script que simula build do Vercel
  - Incluir limpeza de cache, type check, lint, build
  - Adicionar ao package.json como "validate-build"
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 18. Configurar validação TypeScript rigorosa


  - Verificar tsconfig.json para strict mode
  - Executar tsc --noEmit para validar tipos
  - Corrigir erros de tipo encontrados
  - _Requirements: 4.3, 6.4_


- [x] 19. Testar build local vs Vercel




  - Executar build local após todas as correções
  - Comparar output com logs do Vercel
  - Verificar se warnings são idênticos
  - **19.1 Verificar atualização React Query v5**
    - Confirmar que todas as importações usam @tanstack/react-query
    - Verificar se QueryProvider.tsx usa importações corretas
    - Testar se hooks funcionam com nova API (sem onError deprecated)
    - Validar que tratamento de erros usa padrão v5 (useMutation)
  - _Requirements: 4.1, 4.2, 3.1_

- [ ] 20. Implementar testes de regressão
  - Criar testes que verificam funcionalidades críticas
  - Testar componentes modificados (ShareAgentModal, ToolSelector, etc.)
  - Verificar se WebSocket, notifications, executions funcionam
  - _Requirements: 6.1, 6.2, 6.3_

## Fase 5: Prevenção e Documentação

- [ ] 21. Configurar pre-commit hooks
  - Instalar husky e lint-staged
  - Configurar hooks para type check e lint
  - Testar que commits falham se build quebra
  - _Requirements: 6.4, 6.5_

- [ ] 22. Documentar padrões de importação
  - Criar guia de como importar de api-client
  - Documentar padrões para hooks React
  - Criar exemplos de importações corretas
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 23. Criar checklist de deploy
  - Lista de verificações antes de fazer deploy
  - Comandos para validar build local
  - Processo de rollback em caso de erro
  - _Requirements: 5.4, 5.5_

- [ ] 24. Monitorar próximos deploys
  - Verificar se próximo deploy no Vercel é bem-sucedido
  - Documentar qualquer novo erro que apareça
  - Ajustar processo se necessário
  - _Requirements: 4.4, 4.5_