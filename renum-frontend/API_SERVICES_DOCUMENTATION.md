# Documentação dos Serviços de API

Este documento descreve os serviços de API implementados para o frontend do sistema de orquestração de equipes de agentes.

## Estrutura de Arquivos

```
renum-frontend/
├── src/
│   ├── services/
│   │   ├── api-client.ts       # Cliente HTTP para API
│   │   ├── api-error.ts        # Classe de erro personalizada
│   │   ├── api-hooks.ts        # Hooks genéricos para API
│   │   ├── api-types.ts        # Tipos TypeScript para API
│   │   ├── react-query-hooks.ts # Hooks React Query
│   │   ├── query-client.ts     # Configuração do React Query
│   │   └── index.ts            # Exportações
│   ├── contexts/
│   │   ├── AuthContext.tsx     # Contexto de autenticação
│   │   ├── TeamContext.tsx     # Contexto de equipes
│   │   ├── ExecutionContext.tsx # Contexto de execuções
│   │   └── index.tsx           # Exportação e provider combinado
│   ├── hooks/
│   │   ├── useAuth.ts          # Hooks de autenticação
│   │   ├── useTeams.ts         # Hooks para gerenciamento de equipes
│   │   ├── useExecutions.ts    # Hooks para execuções
│   │   └── index.ts            # Exportação de todos os hooks
│   └── providers/
│       ├── QueryProvider.tsx   # Provider para React Query
│       └── index.tsx           # Exportação de todos os providers
```

## Cliente API

O cliente API (`RenumApiClient`) fornece uma interface para interagir com o backend Renum. Ele é implementado usando Axios e inclui métodos para todas as operações necessárias:

### Gerenciamento de Equipes
- `createTeam(teamData)`: Cria uma nova equipe
- `listTeams(options)`: Lista todas as equipes
- `getTeam(teamId)`: Obtém uma equipe por ID
- `updateTeam(teamId, teamData)`: Atualiza uma equipe
- `deleteTeam(teamId)`: Exclui uma equipe

### Gerenciamento de Membros
- `addTeamMember(teamId, memberData)`: Adiciona um membro à equipe
- `updateTeamMember(teamId, agentId, memberData)`: Atualiza um membro da equipe
- `removeTeamMember(teamId, agentId)`: Remove um membro da equipe

### Execuções de Equipe
- `executeTeam(teamId, executionData)`: Executa uma equipe
- `listExecutions(options)`: Lista execuções
- `getExecutionStatus(executionId)`: Obtém status da execução
- `getExecutionResult(executionId)`: Obtém resultado da execução
- `stopExecution(executionId)`: Para uma execução
- `getExecutionLogs(executionId, options)`: Obtém logs de execução

### WebSocket
- `createExecutionMonitor(executionId)`: Cria uma conexão WebSocket para monitorar uma execução

## React Query Hooks

Os hooks React Query (`react-query-hooks.ts`) fornecem uma camada de abstração sobre o cliente API, adicionando cache, revalidação automática e gerenciamento de estado:

### Hooks de Equipes
- `useTeams(options, queryOptions)`: Hook para listar equipes
- `useTeam(teamId, queryOptions)`: Hook para obter uma equipe por ID
- `useCreateTeam(options)`: Hook para criar uma equipe
- `useUpdateTeam(options)`: Hook para atualizar uma equipe
- `useDeleteTeam(options)`: Hook para excluir uma equipe

### Hooks de Membros
- `useAddTeamMember(options)`: Hook para adicionar um membro à equipe
- `useUpdateTeamMember(options)`: Hook para atualizar um membro da equipe
- `useRemoveTeamMember(options)`: Hook para remover um membro da equipe

### Hooks de Execuções
- `useExecutions(options, queryOptions)`: Hook para listar execuções
- `useExecutionStatus(executionId, queryOptions)`: Hook para obter status da execução
- `useExecutionResult(executionId, queryOptions)`: Hook para obter resultado da execução
- `useExecutionLogs(executionId, options, queryOptions)`: Hook para obter logs de execução
- `useExecuteTeam(options)`: Hook para executar uma equipe
- `useStopExecution(options)`: Hook para parar uma execução

## Configuração do React Query

O arquivo `query-client.ts` configura o React Query com opções padrão otimizadas para a aplicação:

- `refetchOnWindowFocus: false`: Não revalida quando a janela ganha foco
- `retry: 1`: Tenta uma vez em caso de falha
- `staleTime: 1000 * 60 * 5`: Considera os dados obsoletos após 5 minutos
- `cacheTime: 1000 * 60 * 30`: Mantém os dados em cache por 30 minutos

Também fornece funções utilitárias:
- `clearQueryCache()`: Limpa o cache do React Query
- `invalidateQueries(queryKey)`: Invalida consultas específicas
- `resetQueries(queryKey)`: Redefine consultas específicas
- `prefetchQuery(queryKey, queryFn)`: Pré-carrega dados
- `setQueryData(queryKey, data)`: Define dados de consulta manualmente
- `getQueryData(queryKey)`: Obtém dados de consulta do cache

## Providers

O arquivo `providers/index.tsx` combina todos os providers necessários para a aplicação:

```jsx
<QueryProvider>
  <AppProviders>
    {children}
  </AppProviders>
</QueryProvider>
```

A ordem é importante: QueryProvider deve envolver AppProviders para que os hooks do React Query possam ser usados dentro dos contextos.

## Uso

### Exemplo de uso com React Query

```tsx
import { useTeams, useCreateTeam } from '../services';

function TeamsList() {
  // Listar equipes com React Query
  const { data, isLoading, error } = useTeams();
  
  // Criar equipe com React Query
  const { mutate, isLoading: isCreating } = useCreateTeam({
    onSuccess: (data) => {
      console.log('Equipe criada:', data);
    }
  });
  
  const handleCreateTeam = () => {
    mutate({
      name: 'Nova Equipe',
      description: 'Descrição da equipe',
      agent_ids: ['agent1', 'agent2'],
      workflow_definition: {
        type: 'sequential',
        agents: [
          {
            agent_id: 'agent1',
            role: 'leader',
            execution_order: 1,
            input: { source: 'initial_prompt' }
          },
          {
            agent_id: 'agent2',
            role: 'member',
            execution_order: 2,
            input: { source: 'agent_result', agent_id: 'agent1' }
          }
        ]
      }
    });
  };
  
  if (isLoading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error.message}</div>;
  
  return (
    <div>
      <h1>Equipes</h1>
      <button onClick={handleCreateTeam} disabled={isCreating}>
        {isCreating ? 'Criando...' : 'Criar Equipe'}
      </button>
      <ul>
        {data?.items.map(team => (
          <li key={team.team_id}>{team.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Exemplo de uso com Context API

```tsx
import { useTeamContext } from '../contexts';

function TeamsList() {
  const { teams, loading, error, fetchTeams, createTeam } = useTeamContext();
  
  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);
  
  const handleCreateTeam = async () => {
    await createTeam({
      name: 'Nova Equipe',
      description: 'Descrição da equipe',
      agent_ids: ['agent1', 'agent2'],
      workflow_definition: {
        type: 'sequential',
        agents: [
          {
            agent_id: 'agent1',
            role: 'leader',
            execution_order: 1,
            input: { source: 'initial_prompt' }
          },
          {
            agent_id: 'agent2',
            role: 'member',
            execution_order: 2,
            input: { source: 'agent_result', agent_id: 'agent1' }
          }
        ]
      }
    });
  };
  
  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error.message}</div>;
  
  return (
    <div>
      <h1>Equipes</h1>
      <button onClick={handleCreateTeam}>Criar Equipe</button>
      <ul>
        {teams.map(team => (
          <li key={team.team_id}>{team.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

## Considerações de Performance

- **Caching**: O React Query fornece cache automático para reduzir requisições desnecessárias.
- **Revalidação**: Configurado para revalidar dados automaticamente com base em intervalos específicos.
- **Prefetching**: Suporte para pré-carregar dados para melhorar a experiência do usuário.
- **Deduplicação**: Requisições idênticas são combinadas para reduzir chamadas à API.
- **Invalidação Inteligente**: Invalidação automática de consultas relacionadas quando os dados são modificados.

## Tratamento de Erros

O cliente API inclui tratamento de erros robusto:
- Interceptor de resposta para capturar e formatar erros da API
- Classe `ApiError` personalizada para representar erros da API
- Métodos utilitários para verificar tipos específicos de erro (não autorizado, proibido, etc.)
- Integração com React Query para gerenciamento de estado de erro