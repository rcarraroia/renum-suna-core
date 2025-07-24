/**
 * API Client for Renum Backend
 * 
 * This module provides a client for interacting with the Renum Backend API.
 * It includes functions for managing teams, team members, and team executions.
 */

import axios from 'axios';

/**
 * API Client class for Renum Backend
 */
class RenumApiClient {
  /**
   * Creates a new API client instance
   * 
   * @param {string} baseUrl - Base URL of the API
   * @param {string} token - Authentication token
   */
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9000/api/v1';
    this.token = token;
    
    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      }
    });
    
    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        // Handle API errors
        const errorMessage = error.response?.data?.detail || error.message;
        console.error(`API Error: ${errorMessage}`);
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Sets the authentication token
   * 
   * @param {string} token - Authentication token
   */
  setToken(token) {
    this.token = token;
    this.client.defaults.headers.Authorization = `Bearer ${token}`;
  }
  
  /**
   * Team Management API
   */
  
  /**
   * Creates a new team
   * 
   * @param {Object} teamData - Team data
   * @returns {Promise<Object>} Created team
   */
  async createTeam(teamData) {
    const response = await this.client.post('/teams', teamData);
    return response.data;
  }
  
  /**
   * Lists all teams
   * 
   * @param {Object} options - Query options
   * @param {number} options.page - Page number
   * @param {number} options.limit - Items per page
   * @param {string} options.nameFilter - Filter by name
   * @param {boolean} options.activeOnly - Include only active teams
   * @returns {Promise<Object>} Paginated list of teams
   */
  async listTeams(options = {}) {
    const { page = 1, limit = 10, nameFilter, activeOnly = true } = options;
    
    const params = {
      page,
      limit,
      name_filter: nameFilter,
      active_only: activeOnly
    };
    
    const response = await this.client.get('/teams', { params });
    return response.data;
  }
  
  /**
   * Gets a team by ID
   * 
   * @param {string} teamId - Team ID
   * @returns {Promise<Object>} Team data
   */
  async getTeam(teamId) {
    const response = await this.client.get(`/teams/${teamId}`);
    return response.data;
  }
  
  /**
   * Updates a team
   * 
   * @param {string} teamId - Team ID
   * @param {Object} teamData - Updated team data
   * @returns {Promise<Object>} Updated team
   */
  async updateTeam(teamId, teamData) {
    const response = await this.client.put(`/teams/${teamId}`, teamData);
    return response.data;
  }
  
  /**
   * Deletes a team
   * 
   * @param {string} teamId - Team ID
   * @returns {Promise<Object>} Response data
   */
  async deleteTeam(teamId) {
    const response = await this.client.delete(`/teams/${teamId}`);
    return response.data;
  }
  
  /**
   * Team Members API
   */
  
  /**
   * Adds a member to a team
   * 
   * @param {string} teamId - Team ID
   * @param {Object} memberData - Member data
   * @returns {Promise<Object>} Updated team
   */
  async addTeamMember(teamId, memberData) {
    const response = await this.client.post(`/teams/${teamId}/members`, memberData);
    return response.data;
  }
  
  /**
   * Updates a team member
   * 
   * @param {string} teamId - Team ID
   * @param {string} agentId - Agent ID
   * @param {Object} memberData - Updated member data
   * @returns {Promise<Object>} Updated team
   */
  async updateTeamMember(teamId, agentId, memberData) {
    const response = await this.client.put(`/teams/${teamId}/members/${agentId}`, memberData);
    return response.data;
  }
  
  /**
   * Removes a member from a team
   * 
   * @param {string} teamId - Team ID
   * @param {string} agentId - Agent ID
   * @returns {Promise<Object>} Updated team
   */
  async removeTeamMember(teamId, agentId) {
    const response = await this.client.delete(`/teams/${teamId}/members/${agentId}`);
    return response.data;
  }
  
  /**
   * Team Execution API
   */
  
  /**
   * Executes a team
   * 
   * @param {string} teamId - Team ID
   * @param {Object} executionData - Execution data
   * @returns {Promise<Object>} Execution response
   */
  async executeTeam(teamId, executionData) {
    const response = await this.client.post(`/teams/${teamId}/execute`, {
      team_id: teamId,
      ...executionData
    });
    return response.data;
  }
  
  /**
   * Lists executions
   * 
   * @param {Object} options - Query options
   * @param {string} options.teamId - Filter by team ID
   * @param {number} options.limit - Items per page
   * @param {number} options.offset - Offset for pagination
   * @returns {Promise<Array>} List of executions
   */
  async listExecutions(options = {}) {
    const { teamId, limit = 10, offset = 0 } = options;
    
    const params = {
      limit,
      offset
    };
    
    if (teamId) {
      params.team_id = teamId;
    }
    
    const response = await this.client.get('/executions', { params });
    return response.data;
  }
  
  /**
   * Gets execution status
   * 
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Execution status
   */
  async getExecutionStatus(executionId) {
    const response = await this.client.get(`/executions/${executionId}/status`);
    return response.data;
  }
  
  /**
   * Gets execution result
   * 
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Execution result
   */
  async getExecutionResult(executionId) {
    const response = await this.client.get(`/executions/${executionId}/result`);
    return response.data;
  }
  
  /**
   * Stops an execution
   * 
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Response data
   */
  async stopExecution(executionId) {
    const response = await this.client.post(`/executions/${executionId}/stop`);
    return response.data;
  }
  
  /**
   * Gets execution logs
   * 
   * @param {string} executionId - Execution ID
   * @param {Object} options - Query options
   * @param {number} options.limit - Maximum number of logs
   * @param {number} options.offset - Offset for pagination
   * @param {Array<string>} options.logTypes - Filter by log types
   * @param {string} options.agentId - Filter by agent ID
   * @returns {Promise<Array>} Execution logs
   */
  async getExecutionLogs(executionId, options = {}) {
    const { limit = 100, offset = 0, logTypes, agentId } = options;
    
    const params = {
      limit,
      offset
    };
    
    if (logTypes) {
      params.log_types = logTypes;
    }
    
    if (agentId) {
      params.agent_id = agentId;
    }
    
    const response = await this.client.get(`/executions/${executionId}/logs`, { params });
    return response.data;
  }
  
  /**
   * API Keys Management
   */
  
  /**
   * Creates a new API key
   * 
   * @param {Object} keyData - API key data
   * @returns {Promise<Object>} Created API key
   */
  async createApiKey(keyData) {
    const response = await this.client.post('/api-keys', keyData);
    return response.data;
  }
  
  /**
   * Lists all API keys
   * 
   * @returns {Promise<Array>} List of API keys
   */
  async listApiKeys() {
    const response = await this.client.get('/api-keys');
    return response.data;
  }
  
  /**
   * Deletes an API key
   * 
   * @param {string} serviceName - Service name
   * @returns {Promise<Object>} Response data
   */
  async deleteApiKey(serviceName) {
    const response = await this.client.delete(`/api-keys/${serviceName}`);
    return response.data;
  }
  
  /**
   * WebSocket Connection
   */
  
  /**
   * Creates a WebSocket connection for monitoring an execution
   * 
   * @param {string} executionId - Execution ID
   * @returns {WebSocket} WebSocket connection
   */
  createExecutionMonitor(executionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const baseUrl = this.baseUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '');
    
    const wsUrl = `${protocol}//${baseUrl || host}/api/v1/ws/executions/${executionId}/monitor?token=${this.token}`;
    
    return new WebSocket(wsUrl);
  }
}

export default RenumApiClient;