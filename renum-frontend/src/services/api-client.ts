/**
 * API Client para Renum Backend
 * 
 * Este módulo fornece um cliente para interagir com a API do Renum Backend.
 * Inclui funções para gerenciar equipes, membros de equipe e execuções de equipe.
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { 
  ApiClientOptions, 
  TeamCreate, 
  TeamUpdate, 
  TeamResponse, 
  PaginatedTeamResponse,
  ListTeamsOptions,
  TeamExecutionCreate,
  TeamExecutionResponse,
  TeamExecutionStatus,
  TeamExecutionResult,
  ExecutionLogEntry,
  GetExecutionLogsOptions,
  ListExecutionsOptions,
  UserApiKeyCreate,
  UserApiKeyResponse,
  ApiErrorResponse
} from './api-types';

/**
 * Classe de cliente API para o Renum Backend
 */
class RenumApiClient {
  private baseUrl: string;
  private token: string | null;
  private client: AxiosInstance;

  /**
   * Cria uma nova instância do cliente API
   * 
   * @param options - Opções de configuração
   */
  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000/api/v1';
    this.token = options.token || null;
    
    // Cria instância axios com configuração padrão
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {})
      }
    });
    
    // Adiciona interceptor de resposta para tratamento de erros
    this.client.interceptors.response.use(
      response => response,
      (error: AxiosError<ApiErrorResponse>) => {
        // Trata erros da API
        const errorMessage = error.response?.data?.detail || error.message;
        console.error(`API Error: ${errorMessage}`);
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Define o token de autenticação
   * 
   * @param token - Token de autenticação
   */
  setToken(token: string): void {
    this.token = token;
    this.client.defaults.headers.Authorization = `Bearer ${token}`;
  }
  
  /**
   * API de Gerenciamento de Equipes
   */
  
  /**
   * Cria uma nova equipe
   * 
   * @param teamData - Dados da equipe
   * @returns Equipe criada
   */
  async createTeam(teamData: TeamCreate): Promise<TeamResponse> {
    const response = await this.client.post<TeamResponse>('/teams', teamData);
    return response.data;
  }
  
  /**
   * Lista todas as equipes
   * 
   * @param options - Opções de consulta
   * @returns Lista paginada de equipes
   */
  async listTeams(options: ListTeamsOptions = {}): Promise<PaginatedTeamResponse> {
    const { page = 1, limit = 10, nameFilter, activeOnly = true } = options;
    
    const params = {
      page,
      limit,
      name_filter: nameFilter,
      active_only: activeOnly
    };
    
    const response = await this.client.get<PaginatedTeamResponse>('/teams', { params });
    return response.data;
  }
  
  /**
   * Obtém uma equipe por ID
   * 
   * @param teamId - ID da equipe
   * @returns Dados da equipe
   */
  async getTeam(teamId: string): Promise<TeamResponse> {
    const response = await this.client.get<TeamResponse>(`/teams/${teamId}`);
    return response.data;
  }
  
  /**
   * Atualiza uma equipe
   * 
   * @param teamId - ID da equipe
   * @param teamData - Dados atualizados da equipe
   * @returns Equipe atualizada
   */
  async updateTeam(teamId: string, teamData: TeamUpdate): Promise<TeamResponse> {
    const response = await this.client.put<TeamResponse>(`/teams/${teamId}`, teamData);
    return response.data;
  }
  
  /**
   * Exclui uma equipe
   * 
   * @param teamId - ID da equipe
   * @returns Dados da resposta
   */
  async deleteTeam(teamId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete<{ success: boolean }>(`/teams/${teamId}`);
    return response.data;
  }
  
  /**
   * API de Membros da Equipe
   */
  
  /**
   * Adiciona um membro a uma equipe
   * 
   * @param teamId - ID da equipe
   * @param memberData - Dados do membro
   * @returns Equipe atualizada
   */
  async addTeamMember(teamId: string, memberData: { agent_id: string; role?: string; execution_order?: number }): Promise<TeamResponse> {
    const response = await this.client.post<TeamResponse>(`/teams/${teamId}/members`, memberData);
    return response.data;
  }
  
  /**
   * Atualiza um membro da equipe
   * 
   * @param teamId - ID da equipe
   * @param agentId - ID do agente
   * @param memberData - Dados atualizados do membro
   * @returns Equipe atualizada
   */
  async updateTeamMember(teamId: string, agentId: string, memberData: { role?: string; execution_order?: number }): Promise<TeamResponse> {
    const response = await this.client.put<TeamResponse>(`/teams/${teamId}/members/${agentId}`, memberData);
    return response.data;
  }
  
  /**
   * Remove um membro de uma equipe
   * 
   * @param teamId - ID da equipe
   * @param agentId - ID do agente
   * @returns Equipe atualizada
   */
  async removeTeamMember(teamId: string, agentId: string): Promise<TeamResponse> {
    const response = await this.client.delete<TeamResponse>(`/teams/${teamId}/members/${agentId}`);
    return response.data;
  }
  
  /**
   * API de Execução de Equipe
   */
  
  /**
   * Executa uma equipe
   * 
   * @param teamId - ID da equipe
   * @param executionData - Dados de execução
   * @returns Resposta de execução
   */
  async executeTeam(teamId: string, executionData: Omit<TeamExecutionCreate, 'team_id'>): Promise<TeamExecutionResponse> {
    const response = await this.client.post<TeamExecutionResponse>(`/teams/${teamId}/execute`, {
      team_id: teamId,
      ...executionData
    });
    return response.data;
  }
  
  /**
   * Lista execuções
   * 
   * @param options - Opções de consulta
   * @returns Lista de execuções
   */
  async listExecutions(options: ListExecutionsOptions = {}): Promise<TeamExecutionResponse[]> {
    const { teamId, limit = 10, offset = 0 } = options;
    
    const params = {
      limit,
      offset
    };
    
    if (teamId) {
      params['team_id'] = teamId;
    }
    
    const response = await this.client.get<TeamExecutionResponse[]>('/executions', { params });
    return response.data;
  }
  
  /**
   * Obtém status da execução
   * 
   * @param executionId - ID da execução
   * @returns Status da execução
   */
  async getExecutionStatus(executionId: string): Promise<TeamExecutionStatus> {
    const response = await this.client.get<TeamExecutionStatus>(`/executions/${executionId}`);
    return response.data;
  }
  
  /**
   * Obtém resultado da execução
   * 
   * @param executionId - ID da execução
   * @returns Resultado da execução
   */
  async getExecutionResult(executionId: string): Promise<TeamExecutionResult> {
    const response = await this.client.get<TeamExecutionResult>(`/executions/${executionId}/result`);
    return response.data;
  }
  
  /**
   * Para uma execução
   * 
   * @param executionId - ID da execução
   * @returns Dados da resposta
   */
  async stopExecution(executionId: string): Promise<{ success: boolean }> {
    const response = await this.client.post<{ success: boolean }>(`/executions/${executionId}/stop`);
    return response.data;
  }
  
  /**
   * Obtém logs de execução
   * 
   * @param executionId - ID da execução
   * @param options - Opções de consulta
   * @returns Logs de execução
   */
  async getExecutionLogs(executionId: string, options: GetExecutionLogsOptions = {}): Promise<ExecutionLogEntry[]> {
    const { limit = 100, offset = 0, logTypes, agentId } = options;
    
    const params = {
      limit,
      offset
    };
    
    if (logTypes) {
      params['log_types'] = logTypes;
    }
    
    if (agentId) {
      params['agent_id'] = agentId;
    }
    
    const response = await this.client.get<ExecutionLogEntry[]>(`/executions/${executionId}/logs`, { params });
    return response.data;
  }
  
  /**
   * Gerenciamento de Chaves API
   */
  
  /**
   * Cria uma nova chave API
   * 
   * @param keyData - Dados da chave API
   * @returns Chave API criada
   */
  async createApiKey(keyData: UserApiKeyCreate): Promise<UserApiKeyResponse> {
    const response = await this.client.post<UserApiKeyResponse>('/api-keys', keyData);
    return response.data;
  }
  
  /**
   * Lista todas as chaves API
   * 
   * @returns Lista de chaves API
   */
  async listApiKeys(): Promise<UserApiKeyResponse[]> {
    const response = await this.client.get<UserApiKeyResponse[]>('/api-keys');
    return response.data;
  }
  
  /**
   * Exclui uma chave API
   * 
   * @param serviceName - Nome do serviço
   * @returns Dados da resposta
   */
  async deleteApiKey(serviceName: string): Promise<{ success: boolean }> {
    const response = await this.client.delete<{ success: boolean }>(`/api-keys/${serviceName}`);
    return response.data;
  }
  
  /**
   * Conexão WebSocket
   */
  
  /**
   * Cria uma conexão WebSocket para monitorar uma execução
   * 
   * @param executionId - ID da execução
   * @returns Conexão WebSocket
   */
  createExecutionMonitor(executionId: string): WebSocket {
    if (typeof window === 'undefined') {
      throw new Error('WebSocket só pode ser criado no navegador');
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const baseUrl = this.baseUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
    
    const wsUrl = `${protocol}//${baseUrl || host}/api/v1/ws/executions/${executionId}/monitor?token=${this.token}`;
    
    return new WebSocket(wsUrl);
  }
}

export default RenumApiClient;