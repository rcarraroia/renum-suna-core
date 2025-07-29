/**
 * Constantes de configuração do WebSocket
 */

export const WEBSOCKET_CONFIG = {
  DEFAULT_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws',
  RECONNECT_INTERVAL: 5000,
  MAX_RECONNECT_ATTEMPTS: 5,
  HEARTBEAT_INTERVAL: 30000,
} as const;

export const WEBSOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  MESSAGE: 'message',
  RECONNECT: 'reconnect',
} as const;