/**
 * Utilitários para manipulação de workflows
 */

import { WorkflowDefinition, WorkflowType, WorkflowAgent, AgentRole } from '../services/api-types';

/**
 * Obtém o nome amigável de um tipo de workflow
 * @param type Tipo de workflow
 * @returns Nome amigável
 */
export function getWorkflowTypeName(type: WorkflowType): string {
  const names: Record<WorkflowType, string> = {
    [WorkflowType.SEQUENTIAL]: 'Sequencial',
    [WorkflowType.PARALLEL]: 'Paralelo',
    [WorkflowType.CONDITIONAL]: 'Condicional'
  };
  
  return names[type] || type;
}

/**
 * Obtém o nome amigável de um papel de agente
 * @param role Papel do agente
 * @returns Nome amigável
 */
export function getAgentRoleName(role: AgentRole): string {
  const names: Record<AgentRole, string> = {
    [AgentRole.LEADER]: 'Líder',
    [AgentRole.COORDINATOR]: 'Coordenador',
    [AgentRole.MEMBER]: 'Membro',
    [AgentRole.REVIEWER]: 'Revisor'
  };
  
  return names[role] || role;
}

/**
 * Obtém a cor associada a um papel de agente
 * @param role Papel do agente
 * @returns Classe CSS de cor
 */
export function getAgentRoleColor(role: AgentRole): string {
  const colors: Record<AgentRole, string> = {
    [AgentRole.LEADER]: 'bg-blue-100 text-blue-800',
    [AgentRole.COORDINATOR]: 'bg-purple-100 text-purple-800',
    [AgentRole.MEMBER]: 'bg-green-100 text-green-800',
    [AgentRole.REVIEWER]: 'bg-orange-100 text-orange-800'
  };
  
  return colors[role] || 'bg-gray-100 text-gray-800';
}

/**
 * Obtém a cor associada a um tipo de workflow
 * @param type Tipo de workflow
 * @returns Classe CSS de cor
 */
export function getWorkflowTypeColor(type: WorkflowType): string {
  const colors: Record<WorkflowType, string> = {
    [WorkflowType.SEQUENTIAL]: 'bg-blue-100 text-blue-800',
    [WorkflowType.PARALLEL]: 'bg-green-100 text-green-800',
    [WorkflowType.CONDITIONAL]: 'bg-purple-100 text-purple-800'
  };
  
  return colors[type] || 'bg-gray-100 text-gray-800';
}

/**
 * Obtém a cor associada a um papel de agente
 * @param role Papel do agente
 * @returns Classe CSS de cor
 */
export function getAgentRoleColor(role: AgentRole): string {
  const colors: Record<AgentRole, string> = {
    [AgentRole.LEADER]: 'bg-blue-100 text-blue-800',
    [AgentRole.COORDINATOR]: 'bg-purple-100 text-purple-800',
    [AgentRole.MEMBER]: 'bg-green-100 text-green-800',
    [AgentRole.REVIEWER]: 'bg-orange-100 text-orange-800'
  };
  
  return colors[role] || 'bg-gray-100 text-gray-800';
}

/**
 * Ordena agentes por ordem de execução
 * @param agents Lista de agentes
 * @returns Lista ordenada
 */
export function sortAgentsByExecutionOrder(agents: WorkflowAgent[]): WorkflowAgent[] {
  return [...agents].sort((a, b) => {
    // Se ambos têm ordem de execução, ordena por ela
    if (a.execution_order !== undefined && b.execution_order !== undefined) {
      return a.execution_order - b.execution_order;
    }
    
    // Se apenas um tem ordem de execução, ele vem primeiro
    if (a.execution_order !== undefined) return -1;
    if (b.execution_order !== undefined) return 1;
    
    // Se nenhum tem ordem de execução, ordena por papel
    const roleOrder: Record<AgentRole, number> = {
      [AgentRole.LEADER]: 1,
      [AgentRole.COORDINATOR]: 2,
      [AgentRole.MEMBER]: 3,
      [AgentRole.REVIEWER]: 4
    };
    
    return (roleOrder[a.role] || 99) - (roleOrder[b.role] || 99);
  });
}

/**
 * Verifica se um workflow é válido
 * @param workflow Definição de workflow
 * @returns Objeto com resultado da validação
 */
export function validateWorkflow(workflow: WorkflowDefinition): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Verifica se há agentes
  if (!workflow.agents || workflow.agents.length === 0) {
    errors.push('O workflow deve ter pelo menos um agente');
  }
  
  // Verifica se há agentes duplicados
  const agentIds = workflow.agents.map(agent => agent.agent_id);
  const uniqueAgentIds = new Set(agentIds);
  if (agentIds.length !== uniqueAgentIds.size) {
    errors.push('O workflow não pode ter agentes duplicados');
  }
  
  // Verifica regras específicas por tipo de workflow
  switch (workflow.type) {
    case WorkflowType.SEQUENTIAL:
      // Verifica se todos os agentes têm ordem de execução
      const missingOrder = workflow.agents.some(agent => agent.execution_order === undefined);
      if (missingOrder) {
        errors.push('Todos os agentes devem ter ordem de execução em um workflow sequencial');
      }
      
      // Verifica se há ordens de execução duplicadas
      const orders = workflow.agents.map(agent => agent.execution_order).filter(Boolean);
      const uniqueOrders = new Set(orders);
      if (orders.length !== uniqueOrders.size) {
        errors.push('Não pode haver agentes com a mesma ordem de execução');
      }
      break;
      
    case WorkflowType.CONDITIONAL:
      // Verifica se há pelo menos um agente com condição
      const hasCondition = workflow.agents.some(agent => agent.conditions && agent.conditions.length > 0);
      if (!hasCondition) {
        errors.push('Pelo menos um agente deve ter condições em um workflow condicional');
      }
      break;
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Obtém uma descrição resumida do workflow
 * @param workflow Definição de workflow
 * @returns Descrição resumida
 */
export function getWorkflowSummary(workflow: WorkflowDefinition): string {
  if (!workflow) return '';
  
  const agentCount = workflow.agents?.length || 0;
  const type = getWorkflowTypeName(workflow.type);
  
  return `${type} com ${agentCount} agente${agentCount !== 1 ? 's' : ''}`;
}