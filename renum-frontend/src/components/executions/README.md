# Componentes de Execução

Este diretório contém componentes React para visualização e monitoramento de execuções de equipes em tempo real.

## Componentes

### ExecutionProgress
Componente básico para exibir o progresso de uma execução.

**Props:**
- `progress: number` - Porcentagem de progresso (0-100)
- `status: string` - Status da execução ('pending', 'running', 'completed', 'failed')
- `currentStep?: string` - Etapa atual da execução
- `totalSteps?: number` - Número total de etapas
- `completedSteps?: number` - Número de etapas concluídas
- `className?: string` - Classes CSS adicionais

**Uso:**
```tsx
<ExecutionProgress
  progress={75}
  status="running"
  currentStep="Processando dados"
  totalSteps={10}
  completedSteps={7}
/>
```

### RealTimeExecutionProgress
Componente avançado que monitora uma execução específica em tempo real via WebSocket.

**Props:**
- `executionId: string` - ID da execução a ser monitorada
- `teamId?: string` - ID da equipe (opcional)
- `onStatusChange?: (status: string) => void` - Callback para mudanças de status
- `onComplete?: (result: any) => void` - Callback para conclusão
- `onError?: (error: string) => void` - Callback para erros
- `className?: string` - Classes CSS adicionais

**Funcionalidades:**
- Monitoramento em tempo real via WebSocket
- Reconexão automática
- Indicadores visuais de conexão
- Exibição de erros e resultados
- Callbacks para eventos importantes

**Uso:**
```tsx
<RealTimeExecutionProgress
  executionId="exec-123"
  teamId="team-456"
  onStatusChange={(status) => console.log('Status:', status)}
  onComplete={(result) => console.log('Resultado:', result)}
  onError={(error) => console.error('Erro:', error)}
/>
```

### ExecutionDashboard
Dashboard completo para visualização de múltiplas execuções com filtros e estatísticas.

**Props:**
- `teamId?: string` - Filtrar por equipe específica
- `userId?: string` - Filtrar por usuário específico
- `className?: string` - Classes CSS adicionais

**Funcionalidades:**
- Visualização de execuções ativas, concluídas e falhadas
- Estatísticas em tempo real
- Filtros por status
- Auto-refresh configurável
- Detalhes expandidos para cada execução

**Uso:**
```tsx
<ExecutionDashboard
  teamId="team-123"
  userId="user-456"
/>
```

### ExecutionNotifications
Componente para exibir notificações relacionadas a execuções.

**Props:**
- `userId?: string` - ID do usuário para filtrar notificações
- `teamId?: string` - ID da equipe para filtrar notificações
- `maxNotifications?: number` - Número máximo de notificações (padrão: 50)
- `autoMarkAsRead?: boolean` - Marcar automaticamente como lida (padrão: false)
- `showToasts?: boolean` - Exibir toasts para novas notificações (padrão: true)
- `className?: string` - Classes CSS adicionais

**Funcionalidades:**
- Notificações em tempo real via WebSocket
- Toasts para novas notificações
- Filtros por tipo de notificação
- Marcação como lida/não lida
- Navegação para execuções relacionadas

**Uso:**
```tsx
<ExecutionNotifications
  userId="user-123"
  teamId="team-456"
  maxNotifications={20}
  showToasts={true}
  autoMarkAsRead={false}
/>
```

## Hooks Relacionados

### useRealTimeExecutions
Hook para gerenciar execuções em tempo real.

**Parâmetros:**
```tsx
interface UseRealTimeExecutionsOptions {
  teamId?: string;
  userId?: string;
  autoSubscribe?: boolean;
  includeCompleted?: boolean;
  maxExecutions?: number;
}
```

**Retorno:**
```tsx
interface UseRealTimeExecutionsReturn {
  executions: ExecutionSummary[];
  activeExecutions: ExecutionSummary[];
  completedExecutions: ExecutionSummary[];
  failedExecutions: ExecutionSummary[];
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  subscribe: (teamId: string) => void;
  unsubscribe: (teamId: string) => void;
  subscribeToExecution: (executionId: string) => void;
  unsubscribeFromExecution: (executionId: string) => void;
  refreshExecutions: () => Promise<void>;
  clearError: () => void;
}
```

**Uso:**
```tsx
const {
  executions,
  activeExecutions,
  isLoading,
  error,
  subscribe,
  refreshExecutions
} = useRealTimeExecutions({
  teamId: 'team-123',
  autoSubscribe: true,
  includeCompleted: false
});
```

## Integração com WebSocket

Todos os componentes utilizam o sistema WebSocket para atualizações em tempo real:

1. **Conexão**: Gerenciada pelo `WebSocketContext`
2. **Canais**: Inscrição em canais específicos (`team_${teamId}`, `execution_${executionId}`)
3. **Eventos**: Escuta de eventos de atualização de execução
4. **Reconexão**: Automática com reinscrição em canais

## Tipos de Eventos WebSocket

### execution_started
Disparado quando uma execução é iniciada.

### execution_updated
Disparado durante o progresso da execução.

### execution_completed
Disparado quando uma execução é concluída com sucesso.

### execution_failed
Disparado quando uma execução falha.

### execution_progress
Disparado para atualizações de progresso específicas.

## Estrutura de Dados

### ExecutionUpdate
```tsx
interface ExecutionUpdate {
  execution_id: string;
  team_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step?: string;
  total_steps?: number;
  completed_steps?: number;
  current_agent?: string;
  total_agents?: number;
  completed_agents?: number;
  error_message?: string;
  result?: any;
  updated_at: string;
}
```

### ExecutionSummary
```tsx
interface ExecutionSummary {
  id: string;
  team_id: string;
  team_name: string;
  status: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  created_by: string;
  error_message?: string;
  result?: any;
}
```

## Exemplos de Uso

### Página de Detalhes da Equipe
```tsx
import { RealTimeTeamExecutions, ExecutionNotifications } from '../components/executions';

function TeamDetailsPage({ teamId }: { teamId: string }) {
  return (
    <div className="space-y-6">
      <RealTimeTeamExecutions
        teamId={teamId}
        onExecutionStart={(execution) => {
          console.log('Nova execução iniciada:', execution);
        }}
      />
      
      <ExecutionNotifications
        teamId={teamId}
        showToasts={true}
        maxNotifications={10}
      />
    </div>
  );
}
```

### Dashboard Geral
```tsx
import { ExecutionDashboard } from '../components/executions';

function DashboardPage() {
  return (
    <div className="container mx-auto py-6">
      <ExecutionDashboard />
    </div>
  );
}
```

### Monitoramento de Execução Específica
```tsx
import { RealTimeExecutionProgress } from '../components/executions';

function ExecutionMonitorPage({ executionId }: { executionId: string }) {
  return (
    <div className="max-w-4xl mx-auto py-6">
      <RealTimeExecutionProgress
        executionId={executionId}
        onComplete={(result) => {
          // Redirecionar ou mostrar resultado
          console.log('Execução concluída:', result);
        }}
        onError={(error) => {
          // Mostrar erro
          console.error('Erro na execução:', error);
        }}
      />
    </div>
  );
}
```

## Considerações de Performance

1. **Limitação de Execuções**: Use `maxExecutions` para limitar o número de execuções carregadas
2. **Auto-refresh**: Configure intervalos apropriados para auto-refresh
3. **Filtros**: Use filtros para reduzir a quantidade de dados processados
4. **Desinscrição**: Sempre desinscreva-se de canais WebSocket quando componentes são desmontados

## Tratamento de Erros

Todos os componentes incluem tratamento robusto de erros:

1. **Erros de Conexão**: Indicadores visuais de status de conexão
2. **Erros de API**: Mensagens de erro amigáveis ao usuário
3. **Reconexão**: Tentativas automáticas de reconexão
4. **Fallbacks**: Estados de carregamento e erro apropriados