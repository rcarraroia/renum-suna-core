/**
 * Type definitions for the Renum API
 */

/**
 * Workflow types
 */
export enum WorkflowType {
  SEQUENTIAL = 'sequential',
  PARALLEL = 'parallel',
  CONDITIONAL = 'conditional',
  PIPELINE = 'pipeline'
}

/**
 * Agent roles
 */
export enum AgentRole {
  LEADER = 'leader',
  MEMBER = 'member',
  COORDINATOR = 'coordinator'
}

/**
 * Execution status
 */
export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  SKIPPED = 'skipped'
}

/**
 * Input source types
 */
export enum InputSource {
  INITIAL_PROMPT = 'initial_prompt',
  AGENT_RESULT = 'agent_result',
  COMBINED = 'combined'
}

/**
 * Input configuration
 */
export interface InputConfig {
  source: InputSource;
  agent_id?: string;
  sources?: Array<{
    type: string;
    agent_id: string;
  }>;
}

/**
 * Agent condition
 */
export interface AgentCondition {
  field: string;
  operator: string;
  value: any;
}

/**
 * Agent configuration in a workflow
 */
export interface WorkflowAgent {
  agent_id: string;
  role?: AgentRole;
  execution_order?: number;
  input: InputConfig;
  conditions?: AgentCondition[];
  timeout?: number;
  retry_config?: Record<string, any>;
}

/**
 * Workflow definition
 */
export interface WorkflowDefinition {
  type: WorkflowType;
  agents: WorkflowAgent[];
  config?: Record<string, any>;
}

/**
 * Team creation request
 */
export interface TeamCreate {
  name: string;
  description?: string;
  agent_ids: string[];
  workflow_definition: WorkflowDefinition;
  user_api_keys?: Record<string, string>;
  team_config?: Record<string, any>;
}

/**
 * Team update request
 */
export interface TeamUpdate {
  name?: string;
  description?: string;
  agent_ids?: string[];
  workflow_definition?: WorkflowDefinition;
  user_api_keys?: Record<string, string>;
  team_config?: Record<string, any>;
  is_active?: boolean;
}

/**
 * Team response
 */
export interface TeamResponse {
  team_id: string;
  user_id: string;
  name: string;
  description?: string;
  agent_ids: string[];
  workflow_definition: WorkflowDefinition;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Paginated team response
 */
export interface PaginatedTeamResponse {
  items: TeamResponse[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Team execution create request
 */
export interface TeamExecutionCreate {
  team_id: string;
  initial_prompt: string;
  user_api_keys?: Record<string, string>;
  execution_config?: Record<string, any>;
}

/**
 * Team execution response
 */
export interface TeamExecutionResponse {
  execution_id: string;
  team_id: string;
  status: ExecutionStatus;
  initial_prompt: string;
  final_result?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

/**
 * Team execution status
 */
export interface TeamExecutionStatus {
  execution_id: string;
  team_id: string;
  status: ExecutionStatus;
  agent_statuses: Record<string, ExecutionStatus>;
  progress: number;
  current_step?: number;
  total_steps: number;
  active_agents: string[];
  completed_agents: string[];
  failed_agents: string[];
  started_at?: string;
  estimated_completion?: string;
  error_message?: string;
  last_updated: string;
}

/**
 * Cost metrics
 */
export interface CostMetrics {
  cost_usd: number;
  cost_breakdown: Record<string, number>;
  pricing_version: string;
}

/**
 * Usage metrics
 */
export interface UsageMetrics {
  model_provider: string;
  model_name: string;
  api_key_type: string;
  tokens_input: number;
  tokens_output: number;
  request_count: number;
  request_data?: Record<string, any>;
  response_data?: Record<string, any>;
}

/**
 * Team execution result
 */
export interface TeamExecutionResult {
  execution_id: string;
  team_id: string;
  status: ExecutionStatus;
  final_result?: Record<string, any>;
  agent_results?: Record<string, any>;
  cost_metrics?: CostMetrics;
  usage_metrics?: Record<string, UsageMetrics>;
  started_at?: string;
  completed_at?: string;
  execution_duration?: number;
}

/**
 * Execution log entry
 */
export interface ExecutionLogEntry {
  timestamp: string;
  level: string;
  agent_id?: string;
  message: string;
  details?: Record<string, any>;
}

/**
 * User API key create request
 */
export interface UserApiKeyCreate {
  service_name: string;
  api_key: string;
}

/**
 * User API key response
 */
export interface UserApiKeyResponse {
  key_id: string;
  user_id: string;
  service_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * API client options
 */
export interface ApiClientOptions {
  baseUrl?: string;
  token?: string;
}

/**
 * List teams options
 */
export interface ListTeamsOptions {
  page?: number;
  limit?: number;
  nameFilter?: string;
  activeOnly?: boolean;
}

/**
 * List executions options
 */
export interface ListExecutionsOptions {
  teamId?: string;
  limit?: number;
  offset?: number;
}

/**
 * Get execution logs options
 */
export interface GetExecutionLogsOptions {
  limit?: number;
  offset?: number;
  logTypes?: string[];
  agentId?: string;
}

/**
 * WebSocket message types
 */
export enum WebSocketMessageType {
  EXECUTION_UPDATE = 'execution_update',
  AGENT_UPDATE = 'agent_update',
  LOG_ENTRY = 'log_entry',
  ERROR = 'error'
}

/**
 * WebSocket message
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
}