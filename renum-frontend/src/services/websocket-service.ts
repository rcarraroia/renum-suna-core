/**
 * Serviço WebSocket para comunicação em tempo real
 */

import {
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketConnectionStatus,
  WebSocketConnectionOptions,
  WebSocketSubscriptionOptions,
  WebSocketPublishOptions,
  WebSocketCommand,
  WebSocketCommandMessage,
} from '../types/websocket';

/**
 * Classe para gerenciar conexões WebSocket
 */
export class WebSocketService {
  private socket: WebSocket | null = null;
  private status: WebSocketConnectionStatus = WebSocketConnectionStatus.DISCONNECTED;
  private url: string;
  private token: string;
  private autoReconnect: boolean;
  private maxReconnectAttempts: number;
  private reconnectInterval: number;
  private heartbeatInterval: number;
  private debug: boolean;
  private reconnectAttempts: number = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private lastHeartbeat: number = 0;
  private messageHandlers: Map<string, Set<(message: WebSocketMessage) => void>> = new Map();
  private subscriptions: Set<string> = new Set();
  private pendingMessages: WebSocketMessage[] = [];
  private onOpenCallback?: (event: Event) => void;
  private onCloseCallback?: (event: CloseEvent) => void;
  private onErrorCallback?: (event: Event) => void;
  private onMessageCallback?: (message: WebSocketMessage) => void;

  /**
   * Construtor
   * @param options Opções de conexão
   */
  constructor(options: WebSocketConnectionOptions) {
    this.url = options.url;
    this.token = options.token;
    this.autoReconnect = options.autoReconnect ?? true;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
    this.reconnectInterval = options.reconnectInterval ?? 1000;
    this.heartbeatInterval = options.heartbeatInterval ?? 30000;
    this.debug = options.debug ?? false;
    this.onOpenCallback = options.onOpen;
    this.onCloseCallback = options.onClose;
    this.onErrorCallback = options.onError;
    this.onMessageCallback = options.onMessage;
  }

  /**
   * Conecta ao servidor WebSocket
   */
  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
      this.log('WebSocket already connected or connecting');
      return;
    }

    this.status = WebSocketConnectionStatus.CONNECTING;
    this.log(`Connecting to WebSocket server: ${this.url}`);

    try {
      // Adiciona o token como parâmetro de consulta
      const urlWithToken = `${this.url}?token=${encodeURIComponent(this.token)}`;
      this.socket = new WebSocket(urlWithToken);

      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      this.log('Error creating WebSocket connection', error);
      this.status = WebSocketConnectionStatus.ERROR;
      this.scheduleReconnect();
    }
  }

  /**
   * Desconecta do servidor WebSocket
   */
  public disconnect(): void {
    this.log('Disconnecting from WebSocket server');
    this.clearTimeouts();

    if (this.socket) {
      // Cancela todas as assinaturas antes de desconectar
      this.subscriptions.forEach(channel => {
        this.unsubscribe(channel);
      });

      this.socket.close();
      this.socket = null;
    }

    this.status = WebSocketConnectionStatus.DISCONNECTED;
  }

  /**
   * Reconecta ao servidor WebSocket
   */
  public reconnect(): void {
    this.log('Reconnecting to WebSocket server');
    this.disconnect();
    this.connect();
  }

  /**
   * Verifica se está conectado
   */
  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Obtém o status da conexão
   */
  public getStatus(): WebSocketConnectionStatus {
    return this.status;
  }

  /**
   * Assina um canal
   * @param options Opções de assinatura
   * @returns Função para cancelar a assinatura
   */
  public subscribe(options: WebSocketSubscriptionOptions): () => void {
    const { channel, onMessage } = options;

    // Registra o handler de mensagens
    if (onMessage) {
      if (!this.messageHandlers.has(channel)) {
        this.messageHandlers.set(channel, new Set());
      }
      this.messageHandlers.get(channel)?.add(onMessage);
    }

    // Adiciona à lista de assinaturas
    this.subscriptions.add(channel);

    // Envia comando de assinatura se conectado
    if (this.isConnected()) {
      const command: WebSocketCommandMessage = {
        type: WebSocketMessageType.COMMAND,
        command: 'subscribe',
        channel,
      };
      this.sendMessage(command);
    } else {
      // Adiciona à lista de mensagens pendentes
      this.pendingMessages.push({
        type: WebSocketMessageType.COMMAND,
        command: 'subscribe',
        channel,
      });
    }

    // Retorna função para cancelar a assinatura
    return () => {
      this.unsubscribe(channel, onMessage);
    };
  }

  /**
   * Cancela a assinatura de um canal
   * @param channel Canal
   * @param handler Handler de mensagens opcional
   */
  public unsubscribe(channel: string, handler?: (message: WebSocketMessage) => void): void {
    // Remove o handler específico se fornecido
    if (handler && this.messageHandlers.has(channel)) {
      this.messageHandlers.get(channel)?.delete(handler);
      
      // Remove o canal se não houver mais handlers
      if (this.messageHandlers.get(channel)?.size === 0) {
        this.messageHandlers.delete(channel);
      }
    } 
    // Remove todos os handlers se não for fornecido um específico
    else if (!handler) {
      this.messageHandlers.delete(channel);
    }

    // Remove da lista de assinaturas
    this.subscriptions.delete(channel);

    // Envia comando de cancelamento de assinatura se conectado
    if (this.isConnected()) {
      const command: WebSocketCommandMessage = {
        type: WebSocketMessageType.COMMAND,
        command: 'unsubscribe',
        channel,
      };
      this.sendMessage(command);
    }
  }

  /**
   * Publica uma mensagem
   * @param options Opções de publicação
   */
  public publish(options: WebSocketPublishOptions): void {
    const { channel, message, requestId } = options;

    if (!channel) {
      this.log('Channel is required for publishing messages');
      return;
    }

    const wsMessage: WebSocketCommandMessage = {
      type: WebSocketMessageType.COMMAND,
      command: 'message',
      channel,
      content: message,
    };

    if (requestId) {
      wsMessage.request_id = requestId;
    }

    this.sendMessage(wsMessage);
  }

  /**
   * Envia um comando
   * @param command Comando
   * @param params Parâmetros
   */
  public sendCommand(command: string, params?: any): void {
    const wsCommand: WebSocketCommandMessage = {
      type: WebSocketMessageType.COMMAND,
      command,
      ...params,
    };

    this.sendMessage(wsCommand);
  }

  /**
   * Envia um ping para manter a conexão ativa
   */
  public ping(): void {
    if (this.isConnected()) {
      this.sendCommand('ping', { data: Date.now() });
    }
  }

  /**
   * Obtém mensagens em buffer
   */
  public getBufferedMessages(): void {
    this.sendCommand('get_buffered_messages');
  }

  /**
   * Limpa mensagens em buffer
   */
  public clearBufferedMessages(): void {
    this.sendCommand('clear_buffered_messages');
  }

  /**
   * Reseta o circuit breaker
   */
  public resetCircuitBreaker(): void {
    this.sendCommand('reset_circuit_breaker');
  }

  /**
   * Registra um handler para um tipo de mensagem específico
   * @param type Tipo de mensagem
   * @param handler Handler
   * @returns Função para remover o handler
   */
  public on(type: WebSocketMessageType | string, handler: (message: WebSocketMessage) => void): () => void {
    const channel = `type:${type}`;

    if (!this.messageHandlers.has(channel)) {
      this.messageHandlers.set(channel, new Set());
    }
    this.messageHandlers.get(channel)?.add(handler);

    return () => {
      if (this.messageHandlers.has(channel)) {
        this.messageHandlers.get(channel)?.delete(handler);
        if (this.messageHandlers.get(channel)?.size === 0) {
          this.messageHandlers.delete(channel);
        }
      }
    };
  }

  /**
   * Manipula evento de abertura de conexão
   * @param event Evento
   */
  private handleOpen(event: Event): void {
    this.log('WebSocket connection established');
    this.status = WebSocketConnectionStatus.CONNECTED;
    this.reconnectAttempts = 0;

    // Inicia o heartbeat
    this.startHeartbeat();

    // Reinscreve em todos os canais
    this.subscriptions.forEach(channel => {
      const command: WebSocketCommandMessage = {
        type: WebSocketMessageType.COMMAND,
        command: 'subscribe',
        channel,
      };
      this.sendMessage(command);
    });

    // Envia mensagens pendentes
    while (this.pendingMessages.length > 0) {
      const message = this.pendingMessages.shift();
      if (message) {
        this.sendMessage(message);
      }
    }

    // Chama o callback de abertura
    if (this.onOpenCallback) {
      this.onOpenCallback(event);
    }
  }

  /**
   * Manipula evento de fechamento de conexão
   * @param event Evento
   */
  private handleClose(event: CloseEvent): void {
    this.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
    this.status = WebSocketConnectionStatus.DISCONNECTED;
    this.clearTimeouts();

    // Chama o callback de fechamento
    if (this.onCloseCallback) {
      this.onCloseCallback(event);
    }

    // Tenta reconectar se necessário
    if (this.autoReconnect && event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Manipula evento de erro
   * @param event Evento
   */
  private handleError(event: Event): void {
    this.log('WebSocket error', event);
    this.status = WebSocketConnectionStatus.ERROR;

    // Chama o callback de erro
    if (this.onErrorCallback) {
      this.onErrorCallback(event);
    }
  }

  /**
   * Manipula evento de mensagem
   * @param event Evento
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;
      this.log('Received message', message);

      // Atualiza o timestamp do último heartbeat
      if (message.type === WebSocketMessageType.HEARTBEAT) {
        this.lastHeartbeat = Date.now();
      }

      // Chama o callback de mensagem global
      if (this.onMessageCallback) {
        this.onMessageCallback(message);
      }

      // Chama os handlers específicos do tipo
      const typeChannel = `type:${message.type}`;
      if (this.messageHandlers.has(typeChannel)) {
        this.messageHandlers.get(typeChannel)?.forEach(handler => {
          handler(message);
        });
      }

      // Chama os handlers específicos do canal
      if (message.channel && this.messageHandlers.has(message.channel)) {
        this.messageHandlers.get(message.channel)?.forEach(handler => {
          handler(message);
        });
      }
    } catch (error) {
      this.log('Error parsing WebSocket message', error);
    }
  }

  /**
   * Envia uma mensagem
   * @param message Mensagem
   */
  private sendMessage(message: WebSocketMessage): void {
    if (!this.isConnected()) {
      this.log('Cannot send message, WebSocket is not connected');
      this.pendingMessages.push(message);
      return;
    }

    try {
      this.socket?.send(JSON.stringify(message));
      this.log('Sent message', message);
    } catch (error) {
      this.log('Error sending WebSocket message', error);
      this.pendingMessages.push(message);
    }
  }

  /**
   * Agenda uma reconexão
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.log('Maximum reconnect attempts reached');
      return;
    }

    this.status = WebSocketConnectionStatus.RECONNECTING;
    this.reconnectAttempts++;

    // Usa backoff exponencial para o intervalo de reconexão
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    this.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Inicia o heartbeat
   */
  private startHeartbeat(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
    }

    this.lastHeartbeat = Date.now();
    this.heartbeatTimeout = setInterval(() => {
      this.ping();

      // Verifica se o servidor está respondendo
      const now = Date.now();
      if (now - this.lastHeartbeat > this.heartbeatInterval * 2) {
        this.log('Heartbeat timeout, reconnecting');
        this.reconnect();
      }
    }, this.heartbeatInterval);
  }

  /**
   * Limpa os timeouts
   */
  private clearTimeouts(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.heartbeatTimeout) {
      clearInterval(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Registra uma mensagem de log
   * @param message Mensagem
   * @param data Dados adicionais
   */
  private log(message: string, data?: any): void {
    if (this.debug) {
      if (data) {
        console.log(`[WebSocketService] ${message}`, data);
      } else {
        console.log(`[WebSocketService] ${message}`);
      }
    }
  }
}

/**
 * Cria uma instância do serviço WebSocket
 * @param options Opções de conexão
 * @returns Instância do serviço WebSocket
 */
export function createWebSocketService(options: WebSocketConnectionOptions): WebSocketService {
  return new WebSocketService(options);
}