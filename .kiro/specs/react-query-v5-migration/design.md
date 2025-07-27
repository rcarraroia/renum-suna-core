# Design Document

## Overview

Esta especificação define o design técnico para a migração completa do React Query (TanStack Query) para a versão 5 nos projetos `renum-frontend` e `renum-admin`. A migração resolverá o erro crítico de parsing (`./src/services/react-query-hooks.ts:134:78 Error: Parsing error: ',' expected.`) e modernizará a base de código para usar as APIs mais recentes e eficientes.

### Análise da Situação Atual

**Estado Atual:**
- `renum-frontend`: Já possui `@tanstack/react-query: ^5.8.4` no package.json
- `renum-admin`: Também possui `@tanstack/react-query: ^5.8.4` no package.json
- **Problema Identificado**: O código está usando sintaxe mista entre v4 e v5, causando erros de parsing

**Problemas Específicos Encontrados:**
1. Uso incorreto de `invalidateQueries` com sintaxe v4 em código v5
2. Callbacks `onError`, `onSuccess`, `onSettled` sendo usadas incorretamente
3. Sintaxe de `useMutation` misturando padrões v4 e v5
4. Configuração de `queryKey` inconsistente

## Architecture

### Estratégia de Migração

A migração seguirá uma abordagem sistemática em três fases:

1. **Fase 1: Correção de Sintaxe Crítica**
   - Corrigir erros de parsing imediatos
   - Atualizar sintaxe de `useMutation`
   - Padronizar uso de `queryKey`

2. **Fase 2: Modernização de APIs**
   - Migrar callbacks para novos padrões v5
   - Atualizar configurações do QueryClient
   - Implementar tratamento de erros robusto

3. **Fase 3: Otimização e Validação**
   - Aplicar otimizações específicas da v5
   - Implementar testes de validação
   - Documentar padrões estabelecidos

### Principais Mudanças da v5

**1. Sintaxe de useMutation**
```typescript
// v4 (Incorreto)
useMutation(mutationFn, {
  onSuccess: () => {},
  onError: () => {}
})

// v5 (Correto)
useMutation({
  mutationFn: () => {},
  onSuccess: () => {},
  onError: () => {}
})
```

**2. invalidateQueries**
```typescript
// v4 (Incorreto)
queryClient.invalidateQueries(queryKey)

// v5 (Correto)
queryClient.invalidateQueries({ queryKey })
```

**3. Tratamento de Erros**
```typescript
// v5 - Usando error return
const { data, error, isError } = useQuery({
  queryKey: ['key'],
  queryFn: fetchData
})

// v5 - Configuração global
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      throwOnError: true // ou false conforme necessário
    }
  }
})
```

## Components and Interfaces

### Arquivos Principais a Serem Migrados

**renum-frontend:**
1. `src/services/react-query-hooks.ts` - Hook principal com erros críticos
2. `src/services/query-client.ts` - Configuração do QueryClient
3. `src/providers/QueryProvider.tsx` - Provider principal
4. `src/services/agent-hooks.ts` - Hooks de agentes
5. `src/hooks/useAuth.ts` - Hooks de autenticação
6. `src/hooks/useExecutions.ts` - Hooks de execuções
7. `src/hooks/useTeams.ts` - Hooks de equipes

**renum-admin:**
1. Todos os arquivos que usam React Query (a ser identificado durante implementação)
2. Configurações de QueryClient
3. Providers e contextos

### Interface de Migração

```typescript
// Padrão v5 para hooks
interface QueryHookV5<TData, TError = Error> {
  queryKey: QueryKey;
  queryFn: QueryFunction<TData>;
  enabled?: boolean;
  staleTime?: number;
  gcTime?: number; // anteriormente cacheTime
  refetchInterval?: number | false;
  throwOnError?: boolean;
}

interface MutationHookV5<TData, TError, TVariables> {
  mutationFn: MutationFunction<TData, TVariables>;
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: TError, variables: TVariables) => void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables) => void;
}
```

## Data Models

### Estrutura de Configuração

```typescript
// Configuração do QueryClient v5
interface QueryClientConfig {
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: boolean;
      retry: number | ((failureCount: number, error: Error) => boolean);
      staleTime: number;
      gcTime: number; // substitui cacheTime
      throwOnError?: boolean;
    };
    mutations: {
      retry: number | ((failureCount: number, error: Error) => boolean);
      throwOnError?: boolean;
    };
  };
}

// Estrutura de Query Keys
interface QueryKeys {
  teams: string;
  team: (id: string) => string[];
  executions: string;
  teamExecutions: (teamId: string) => string[];
  execution: (id: string) => string[];
  executionStatus: (id: string) => string[];
  executionResult: (id: string) => string[];
  executionLogs: (id: string) => string[];
  apiKeys: string;
}
```

### Padrões de Tratamento de Erros

```typescript
// Padrão para tratamento de erros v5
interface ErrorHandlingPattern {
  // Nível de hook individual
  useQueryWithError: {
    throwOnError: boolean;
    onError?: (error: Error) => void;
  };
  
  // Nível global via QueryClient
  globalErrorHandling: {
    defaultOptions: {
      queries: {
        throwOnError: (error: Error, query: Query) => boolean;
      };
      mutations: {
        throwOnError: (error: Error, mutation: Mutation) => boolean;
      };
    };
  };
}
```

## Error Handling

### Estratégia de Tratamento de Erros v5

**1. Tratamento Local (Nível de Hook)**
```typescript
const { data, error, isError } = useQuery({
  queryKey: ['teams'],
  queryFn: fetchTeams,
  throwOnError: false // Permite captura local do erro
});

// Tratamento manual do erro
if (isError) {
  console.error('Erro ao carregar equipes:', error);
  // Lógica de tratamento específica
}
```

**2. Tratamento Global (Nível de QueryClient)**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      throwOnError: (error, query) => {
        // Lógica para decidir se deve lançar erro globalmente
        return error.status >= 500; // Só lança erros de servidor
      }
    },
    mutations: {
      throwOnError: (error, mutation) => {
        // Lógica específica para mutações
        return false; // Permite tratamento local
      }
    }
  }
});
```

**3. Error Boundaries**
```typescript
// Componente para capturar erros lançados pelo React Query
class QueryErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (error.name === 'QueryError') {
      // Tratamento específico para erros de query
      console.error('Query Error:', error);
    }
  }
}
```

### Migração de Callbacks

**Padrão Atual (Problemático):**
```typescript
// Sintaxe incorreta que causa parsing error
useMutation(
  mutationFn,
  {
    onSuccess: () => {},
    onError: () => {}, // Esta vírgula causa o erro de parsing
  }
);
```

**Padrão v5 (Correto):**
```typescript
useMutation({
  mutationFn,
  onSuccess: (data, variables, context) => {
    // Tratamento de sucesso
  },
  onError: (error, variables, context) => {
    // Tratamento de erro
  },
  onSettled: (data, error, variables, context) => {
    // Sempre executado
  }
});
```

## Testing Strategy

### Estratégia de Testes para Migração

**1. Testes de Regressão**
```typescript
// Testes para garantir que funcionalidades existentes continuem funcionando
describe('React Query v5 Migration', () => {
  test('useTeams hook should fetch teams correctly', async () => {
    const { result } = renderHook(() => useTeams());
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeDefined();
  });

  test('useCreateTeam mutation should work correctly', async () => {
    const { result } = renderHook(() => useCreateTeam());
    const teamData = { name: 'Test Team', description: 'Test' };
    
    act(() => {
      result.current.mutate(teamData);
    });
    
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
```

**2. Testes de Tratamento de Erros**
```typescript
describe('Error Handling v5', () => {
  test('should handle query errors correctly', async () => {
    // Mock API para retornar erro
    server.use(
      rest.get('/api/teams', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server Error' }));
      })
    );

    const { result } = renderHook(() => useTeams());
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  test('should handle mutation errors correctly', async () => {
    server.use(
      rest.post('/api/teams', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({ error: 'Bad Request' }));
      })
    );

    const { result } = renderHook(() => useCreateTeam());
    
    act(() => {
      result.current.mutate({ name: 'Test' });
    });
    
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
```

**3. Testes de Performance**
```typescript
describe('Performance v5', () => {
  test('should have improved bundle size', () => {
    // Teste para verificar redução do bundle size
    const bundleSize = getBundleSize();
    expect(bundleSize).toBeLessThan(PREVIOUS_BUNDLE_SIZE);
  });

  test('should have optimized re-renders', async () => {
    const renderCount = trackRenders();
    const { result } = renderHook(() => useTeams());
    
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(renderCount.current).toBeLessThanOrEqual(EXPECTED_RENDER_COUNT);
  });
});
```

### Validação de Build

**Script de Validação:**
```typescript
// scripts/validate-react-query-v5.js
const { execSync } = require('child_process');

function validateBuild() {
  try {
    // Tenta fazer build
    execSync('npm run build', { stdio: 'inherit' });
    console.log('✅ Build successful - React Query v5 migration complete');
    return true;
  } catch (error) {
    console.error('❌ Build failed - Migration incomplete');
    console.error(error.message);
    return false;
  }
}

function validateSyntax() {
  // Verifica se não há uso de sintaxe v4 depreciada
  const deprecatedPatterns = [
    'useMutation\\(',  // v4 syntax
    'invalidateQueries\\([^{]', // v4 syntax
    'cacheTime:', // renamed to gcTime
  ];
  
  // Implementar verificação de padrões depreciados
}
```

## Implementation Phases

### Fase 1: Correção Crítica (Prioridade Máxima)

**Objetivo:** Resolver o erro de parsing imediato
**Duração Estimada:** 2-4 horas

1. Corrigir sintaxe de `useMutation` em `react-query-hooks.ts`
2. Padronizar uso de `invalidateQueries`
3. Remover vírgulas desnecessárias que causam parsing errors
4. Validar build local

### Fase 2: Modernização Completa

**Objetivo:** Implementar todas as APIs v5 corretamente
**Duração Estimada:** 1-2 dias

1. Migrar todos os hooks para sintaxe v5
2. Implementar tratamento de erros robusto
3. Atualizar configurações do QueryClient
4. Aplicar em ambos os projetos (frontend e admin)

### Fase 3: Otimização e Validação

**Objetivo:** Garantir qualidade e performance
**Duração Estimada:** 1 dia

1. Implementar testes de validação
2. Otimizar configurações para performance
3. Documentar padrões estabelecidos
4. Validar em ambiente de produção

## Migration Checklist

### Checklist de Migração Obrigatória

**Sintaxe e APIs:**
- [ ] Corrigir sintaxe de `useMutation` para formato v5
- [ ] Atualizar todas as chamadas de `invalidateQueries`
- [ ] Substituir `cacheTime` por `gcTime`
- [ ] Padronizar estrutura de `queryKey`

**Tratamento de Erros:**
- [ ] Implementar tratamento de erros v5
- [ ] Configurar error handling global
- [ ] Migrar callbacks `onError`, `onSuccess`, `onSettled`
- [ ] Testar cenários de erro

**Configuração:**
- [ ] Atualizar configuração do QueryClient
- [ ] Verificar compatibilidade de dependências
- [ ] Configurar DevTools v5
- [ ] Validar providers

**Testes e Validação:**
- [ ] Implementar testes de regressão
- [ ] Validar build local e produção
- [ ] Testar performance
- [ ] Documentar mudanças

**Aplicação em Projetos:**
- [ ] Migrar `renum-frontend` completamente
- [ ] Migrar `renum-admin` completamente
- [ ] Sincronizar padrões entre projetos
- [ ] Validar consistência

Esta migração é **OBRIGATÓRIA** e **NÃO NEGOCIÁVEL** para resolver o erro crítico de parsing e modernizar a base de código conforme as melhores práticas atuais.