/**
 * Utilitários para validação de formulários
 */

import { TeamCreate, WorkflowDefinition, WorkflowType } from '../services/api-types';

/**
 * Valida os dados de criação de equipe
 * @param data Dados da equipe
 * @returns Objeto com erros, se houver
 */
export function validateTeamCreate(data: TeamCreate): Record<string, string> {
  const errors: Record<string, string> = {};
  
  // Valida o nome
  if (!data.name?.trim()) {
    errors.name = 'O nome da equipe é obrigatório';
  } else if (data.name.length < 3) {
    errors.name = 'O nome deve ter pelo menos 3 caracteres';
  } else if (data.name.length > 100) {
    errors.name = 'O nome deve ter no máximo 100 caracteres';
  }
  
  // Valida a descrição
  if (!data.description?.trim()) {
    errors.description = 'A descrição da equipe é obrigatória';
  } else if (data.description.length > 500) {
    errors.description = 'A descrição deve ter no máximo 500 caracteres';
  }
  
  // Valida os agentes
  if (!data.agent_ids || data.agent_ids.length === 0) {
    errors.agents = 'Selecione pelo menos um agente';
  } else if (data.agent_ids.length > 10) {
    errors.agents = 'Uma equipe pode ter no máximo 10 agentes';
  }
  
  // Valida o workflow
  const workflowErrors = validateWorkflowDefinition(data.workflow_definition);
  if (workflowErrors) {
    errors.workflow = workflowErrors;
  }
  
  return errors;
}

/**
 * Valida a definição de workflow
 * @param workflow Definição de workflow
 * @returns Mensagem de erro, se houver
 */
export function validateWorkflowDefinition(workflow: WorkflowDefinition): string | null {
  if (!workflow) {
    return 'A definição de workflow é obrigatória';
  }
  
  if (!workflow.type) {
    return 'O tipo de workflow é obrigatório';
  }
  
  if (!workflow.agents || workflow.agents.length === 0) {
    return 'O workflow deve ter pelo menos um agente';
  }
  
  // Verifica se há agentes duplicados
  const agentIds = workflow.agents.map(agent => agent.agent_id);
  const uniqueAgentIds = new Set(agentIds);
  if (agentIds.length !== uniqueAgentIds.size) {
    return 'O workflow não pode ter agentes duplicados';
  }
  
  // Verifica regras específicas por tipo de workflow
  switch (workflow.type) {
    case WorkflowType.SEQUENTIAL:
      // Verifica se todos os agentes têm ordem de execução
      const missingOrder = workflow.agents.some(agent => agent.execution_order === undefined);
      if (missingOrder) {
        return 'Todos os agentes devem ter ordem de execução em um workflow sequencial';
      }
      
      // Verifica se há ordens de execução duplicadas
      const orders = workflow.agents.map(agent => agent.execution_order).filter(Boolean);
      const uniqueOrders = new Set(orders);
      if (orders.length !== uniqueOrders.size) {
        return 'Não pode haver agentes com a mesma ordem de execução';
      }
      break;
  }
  
  return null;
}