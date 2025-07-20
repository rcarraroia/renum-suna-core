# Plano de Implementação de Testes para o Frontend Renum

## Visão Geral

Este documento descreve o plano para implementação de testes unitários e de integração para os componentes do frontend da plataforma Renum. O objetivo é garantir a qualidade, estabilidade e manutenibilidade do código através de uma cobertura de testes adequada.

## Ferramentas e Tecnologias

- **Jest**: Framework de testes principal
- **React Testing Library**: Para testes de componentes React
- **Mock Service Worker (MSW)**: Para simular chamadas de API
- **Jest-Axe**: Para testes de acessibilidade
- **Testing Library User Event**: Para simular interações do usuário

## Estrutura de Testes

Os testes serão organizados seguindo a estrutura do projeto:

```
renum-frontend/
  ├── src/
  │   ├── components/
  │   │   ├── __tests__/
  │   │   │   ├── ComponentName.test.tsx
  │   ├── hooks/
  │   │   ├── __tests__/
  │   │   │   ├── hookName.test.ts
  │   ├── lib/
  │   │   ├── __tests__/
  │   │   │   ├── utilName.test.ts
  │   ├── pages/
  │   │   ├── __tests__/
  │   │   │   ├── pageName.test.tsx
```

## Tipos de Testes

1. **Testes Unitários**: Testam componentes, hooks e funções isoladamente
2. **Testes de Integração**: Testam a interação entre múltiplos componentes
3. **Testes de Snapshot**: Verificam mudanças na UI
4. **Testes de Acessibilidade**: Verificam conformidade com padrões de acessibilidade

## Priorização de Componentes

Os componentes serão testados na seguinte ordem de prioridade:

### Prioridade Alta
1. Componentes de autenticação (login, registro)
2. Componentes de criação de agentes
3. Componentes de chat
4. Hooks críticos (useChat, useAuth)
5. Utilitários de API e estado

### Prioridade Média
1. Componentes de UI reutilizáveis
2. Componentes de dashboard
3. Componentes de visualização de agentes
4. Hooks secundários

### Prioridade Baixa
1. Componentes puramente visuais
2. Utilitários auxiliares
3. Páginas estáticas

## Plano de Implementação

### Fase 1: Setup e Componentes Críticos

1. **Setup do Ambiente de Testes**
   - Configurar Jest e React Testing Library
   - Configurar Mock Service Worker para simular API
   - Criar helpers e mocks comuns

2. **Testes para Componentes de Autenticação**
   - Login.tsx
   - Register.tsx
   - useAuthStore

3. **Testes para Componentes de UI Críticos**
   - Button.tsx
   - Input.tsx
   - Alert.tsx
   - Select.tsx

### Fase 2: Componentes de Agentes e Chat

1. **Testes para Componentes de Criação de Agentes**
   - KnowledgeBaseSelector.tsx
   - ToolSelector.tsx
   - Página de criação de agentes (new.tsx)

2. **Testes para Componentes de Chat**
   - ChatInterface.tsx
   - ToolUsageDisplay.tsx
   - ChatErrorHandler.tsx
   - useChat.ts

### Fase 3: Componentes de Dashboard e Visualização

1. **Testes para Componentes de Dashboard**
   - AgentCard.tsx
   - Sidebar.tsx
   - Layout.tsx

2. **Testes para Componentes de Visualização**
   - Página de detalhes do agente
   - Componentes de métricas

### Fase 4: Hooks, Utilitários e Testes de Integração

1. **Testes para Hooks**
   - useToast.ts
   - Outros hooks personalizados

2. **Testes para Utilitários**
   - api-client.ts
   - utils.ts

3. **Testes de Integração**
   - Fluxo de criação de agente
   - Fluxo de chat
   - Fluxo de autenticação

## Padrões de Teste

### Padrão para Testes de Componentes

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Component from '../Component';

describe('Component', () => {
  it('should render correctly', () => {
    render(<Component />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should handle user interactions', async () => {
    const handleClick = jest.fn();
    render(<Component onClick={handleClick} />);
    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Padrão para Testes de Hooks

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import useCustomHook from '../useCustomHook';

describe('useCustomHook', () => {
  it('should return initial state', () => {
    const { result } = renderHook(() => useCustomHook());
    expect(result.current.value).toBe(initialValue);
  });

  it('should update state when action is called', () => {
    const { result } = renderHook(() => useCustomHook());
    act(() => {
      result.current.setValue('new value');
    });
    expect(result.current.value).toBe('new value');
  });
});
```

## Metas de Cobertura

- **Componentes críticos**: 90% de cobertura
- **Hooks e utilitários**: 85% de cobertura
- **Componentes de UI**: 75% de cobertura
- **Cobertura geral**: 80% de cobertura

## Integração com CI/CD

- Configurar GitHub Actions para executar testes em cada PR
- Bloquear merges se os testes falharem
- Gerar relatórios de cobertura

## Próximos Passos

1. Configurar o ambiente de testes
2. Implementar testes para componentes de autenticação
3. Implementar testes para componentes de UI críticos
4. Expandir para outros componentes seguindo a ordem de prioridade

---

Última atualização: 19/07/2025