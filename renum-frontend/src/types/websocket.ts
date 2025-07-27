/**
 * Tipos para WebSocket
 */

/**
 * Tipo de mensagem WebSocket
 */
export enum WebSocketMessageType {
  NOTIFICATION = 'notification',
  EXECUTION_UPDATE = 'execution_update',
  SYSTEM_EVENT = 'system_event',
  COMMAND = 'command',
  RESPONSE = 'response',
  HEARTBEAT = 'heartbeat',
  ERROR = 'error',
  CONNECTION_ESTABLISHED = 'connection_established',
  SUBSCRIPTION_SUCCESS = 'subscription_success',
  UNSUBSCRIPTION_SUCCESS = 'unsubscription_success',
  RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded',
  BUFFERED_MESSAGES = 'buffered_messages',
  BUFFERED_MESSAGES_CLEARED = 'buffered_messages_cleared',
  CIRCUIT_BREAKER_RESET = 'circuit_breaker_reset',
  CHANNEL_JOINED = 'channel_joined',
  CHANNEL_LEFT = 'channel_left',
  CHANNEL_SUBSCRIBERS = 'channel_subscribers',
  CHANNEL_MESSAGE = 'channel_message',
  ROOM_JOINED = 'room_joined',
  ROOM_LEFT = 'room_left',
  ROOM_MEMBERS = 'room_members',
  ROOM_MESSAGE = 'room_message',
  ROOM_EVENT = 'room_event',
  DIRECT_MESSAGE = 'direct_message',
  USER_SUBSCRIPTIONS = 'user_subscriptions',
  PONG = 'pong',
}

/**
 * Status de conexão WebSocket
 */
export enum WebSocketConnectionStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

/**
 * Mensagem WebSocket base
 */
export interface WebSocketMessage {
  type: WebSocketMessageType | string;
  timestamp?: string;
  [key: string]: any;
}

/**
 * Notificação WebSocket
 */
export interface WebSocketNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  status: 'read' | 'unread';
  created_at: string;
  metadata?: {
    execution_id?: string;
    team_id?: string;
    team_name?: string;
    [key: string]: any;
  };
  action?: {
    type: string;
    payload: any;
  };
}

/**
 * Mensagem de notificação WebSocket
 */
export interface WebSocketNotificationMessage extends WebSocketMessage {
  type: WebSocketMessageType.NOTIFICATION;
  data: WebSocketNotification;
}

/**
 * Atualização de execução WebSocket
 */
export interface WebSocketExecutionUpdate {
  execution_id: string;
  team_id: string;
  status: string;
  progress: number;
  current_step?: string;
  result?: any;
  error?: string;
  updated_at: string;
}

/**
 * Mensagem de atualização de execução WebSocket
 */
export interface WebSocketExecutionUpdateMessage extends WebSocketMessage {
  type: WebSocketMessageType.EXECUTION_UPDATE;
  data: WebSocketExecutionUpdate;
}

/**
 * Comando WebSocket
 */
export interface WebSocketCommand {
  command: string;
  params?: any;
}

/**
 * Mensagem de comando WebSocket
 */
export interface WebSocketCommandMessage extends WebSocketMessage {
  type: WebSocketMessageType.COMMAND;
  command: string;
  [key: string]: any;
}

/**
 * Resposta WebSocket
 */
export interface WebSocketResponse {
  request_id?: string;
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * Mensagem de resposta WebSocket
 */
export interface WebSocketResponseMessage extends WebSocketMessage {
  type: WebSocketMessageType.RESPONSE;
  request_id?: string;
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * Opções de conexão WebSocket
 */
export interface WebSocketConnectionOptions {
  url: string;
  token: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  debug?: boolean;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

/**
 * Opções de assinatura WebSocket
 */
export interface WebSocketSubscriptionOptions {
  channel: string;
  onMessage?: (message: WebSocketMessage) => void;
}

/**
 * Opções de publicação WebSocket
 */
export interface WebSocketPublishOptions {
  channel?: string;
  message: any;
  requestId?: string;
}

/**
 * Estatísticas de conexão WebSocket
 */
export interface WebSocketStats {
  totalConnections: number;
  activeUsers: number;
  channels: Record<string, number>;
  connectionRate: number;
  messageRate: number;
  uptime: number;
}

/**
 * Informações de limite de taxa WebSocket
 */
export interface WebSocketRateLimitInfo {
  allowed: boolean;
  global: {
    allowed: boolean;
    remaining: number;
    reset: number;
  };
  user: {
    allowed: boolean;
    remaining: number;
    reset: number;
  };
  ip: {
    allowed: boolean;
    remaining: number;
    reset: number;
  };
  circuit: {
    allowed: boolean;
    state: string;
  };
}

/**
 * Mensagem de limite de taxa excedido WebSocket
 */
export interface WebSocketRateLimitExceededMessage extends WebSocketMessage {
  type: WebSocketMessageType.RATE_LIMIT_EXCEEDED;
  message: string;
  details: WebSocketRateLimitInfo;
}

/**
 * Mensagem de conexão estabelecida WebSocket
 */
export interface WebSocketConnectionEstablishedMessage extends WebSocketMessage {
  type: WebSocketMessageType.CONNECTION_ESTABLISHED;
  user_id: string;
  message: string;
}

/**
 * Mensagem de sucesso de assinatura WebSocket
 */
export interface WebSocketSubscriptionSuccessMessage extends WebSocketMessage {
  type: WebSocketMessageType.SUBSCRIPTION_SUCCESS;
  channel: string;
}

/**
 * Mensagem de sucesso de cancelamento de assinatura WebSocket
 */
export interface WebSocketUnsubscriptionSuccessMessage extends WebSocketMessage {
  type: WebSocketMessageType.UNSUBSCRIPTION_SUCCESS;
  channel: string;
}

/**
 * Mensagem de mensagens em buffer WebSocket
 */
export interface WebSocketBufferedMessagesMessage extends WebSocketMessage {
  type: WebSocketMessageType.BUFFERED_MESSAGES;
  count: number;
  messages: WebSocketMessage[];
}

/**
 * Mensagem de canal WebSocket
 */
export interface WebSocketChannelMessage extends WebSocketMessage {
  type: WebSocketMessageType.CHANNEL_MESSAGE;
  channel: string;
  sender: string;
  content: any;
}

/**
 * Mensagem de sala WebSocket
 */
export interface WebSocketRoomMessage extends WebSocketMessage {
  type: WebSocketMessageType.ROOM_MESSAGE;
  room: string;
  sender: string;
  content: any;
}

/**
 * Mensagem direta WebSocket
 */
export interface WebSocketDirectMessage extends WebSocketMessage {
  type: WebSocketMessageType.DIRECT_MESSAGE;
  sender: string;
  content: any;
}

/**
 * Mensagem de assinaturas de usuário WebSocket
 */
export interface WebSocketUserSubscriptionsMessage extends WebSocketMessage {
  type: WebSocketMessageType.USER_SUBSCRIPTIONS;
  subscriptions: string[];
  rooms: string[];
}

/**
 * Mensagem de heartbeat WebSocket
 */
export interface WebSocketHeartbeatMessage extends WebSocketMessage {
  type: WebSocketMessageType.HEARTBEAT;
  timestamp: string;
}

/**
 * Mensagem de erro WebSocket
 */
export interface WebSocketErrorMessage extends WebSocketMessage {
  type: WebSocketMessageType.ERROR;
  message: string;
  code?: number;
  details?: any;
}