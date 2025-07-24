/**
 * Hook para gerenciar canais e salas WebSocket
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketMessage } from '../types/websocket';

/**
 * Opções do hook useWebSocketChannel
 */
interface UseWebSocketChannelOptions {
  autoSubscribe?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
}

/**
 * Hook para gerenciar um canal WebSocket
 * @param channelName Nome do canal
 * @param options Opções
 * @returns Objeto com mensagens e funções auxiliares
 */
export function useWebSocketChannel(
  channelName: string,
  options: UseWebSocketChannelOptions = {}
) {
  const {
    autoSubscribe = true,
    onMessage,
  } = options;

  const { subscribe, unsubscribe, publish, sendCommand } = useWebSocketContext();
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [subscribers, setSubscribers] = useState<string[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);

  // Inscreve-se no canal
  const subscribeToChannel = useCallback(() => {
    if (isSubscribed || !channelName) return;

    const unsubscribeFunc = subscribe(channelName, (message) => {
      // Adiciona a mensagem à lista
      if (message.type === WebSocketMessageType.CHANNEL_MESSAGE) {
        setMessages((prev) => [...prev, message]);
      }

      // Atualiza a lista de assinantes
      if (message.type === WebSocketMessageType.CHANNEL_SUBSCRIBERS && message.subscribers) {
        setSubscribers(message.subscribers);
      }

      // Chama o callback de mensagem
      if (onMessage) {
        onMessage(message);
      }
    });

    // Solicita a lista de assinantes
    sendCommand('get_subscribers', { channel: channelName });

    setIsSubscribed(true);

    return unsubscribeFunc;
  }, [channelName, subscribe, sendCommand, onMessage, isSubscribed]);

  // Cancela a inscrição no canal
  const unsubscribeFromChannel = useCallback(() => {
    if (!isSubscribed || !channelName) return;

    unsubscribe(channelName);
    setIsSubscribed(false);
    
    // Envia comando para cancelar a inscrição no servidor
    sendCommand('leave', { channel: channelName });
  }, [channelName, unsubscribe, sendCommand, isSubscribed]);

  // Publica uma mensagem no canal
  const sendMessage = useCallback((content: any) => {
    if (!channelName) return;

    publish(channelName, {
      type: 'message',
      content,
    });
  }, [channelName, publish]);

  // Auto-inscrição
  useEffect(() => {
    if (autoSubscribe && channelName && !isSubscribed) {
      const unsubscribeFunc = subscribeToChannel();
      return () => {
        if (unsubscribeFunc) unsubscribeFunc();
      };
    }
    return undefined;
  }, [autoSubscribe, channelName, isSubscribed, subscribeToChannel]);

  return {
    messages,
    subscribers,
    isSubscribed,
    subscribeToChannel,
    unsubscribeFromChannel,
    sendMessage,
  };
}

/**
 * Opções do hook useWebSocketRoom
 */
interface UseWebSocketRoomOptions {
  autoJoin?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onJoin?: (userId: string) => void;
  onLeave?: (userId: string) => void;
}

/**
 * Hook para gerenciar uma sala WebSocket
 * @param roomName Nome da sala
 * @param options Opções
 * @returns Objeto com mensagens e funções auxiliares
 */
export function useWebSocketRoom(
  roomName: string,
  options: UseWebSocketRoomOptions = {}
) {
  const {
    autoJoin = true,
    onMessage,
    onJoin,
    onLeave,
  } = options;

  const { subscribe, unsubscribe, publish, sendCommand } = useWebSocketContext();
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [members, setMembers] = useState<string[]>([]);
  const [isJoined, setIsJoined] = useState(false);

  // Entra na sala
  const joinRoom = useCallback(() => {
    if (isJoined || !roomName) return;

    const channel = `ws:room:${roomName}`;
    
    const unsubscribeFunc = subscribe(channel, (message) => {
      // Adiciona a mensagem à lista
      if (message.type === WebSocketMessageType.ROOM_MESSAGE) {
        setMessages((prev) => [...prev, message]);
      }

      // Atualiza a lista de membros
      if (message.type === WebSocketMessageType.ROOM_MEMBERS && message.members) {
        setMembers(message.members);
      }

      // Processa eventos de entrada/saída
      if (message.type === WebSocketMessageType.ROOM_EVENT) {
        if (message.event === 'join' && onJoin && message.user_id) {
          onJoin(message.user_id);
        } else if (message.event === 'leave' && onLeave && message.user_id) {
          onLeave(message.user_id);
        }
      }

      // Chama o callback de mensagem
      if (onMessage) {
        onMessage(message);
      }
    });

    // Envia comando para entrar na sala
    sendCommand('join_room', { room: roomName });

    // Solicita a lista de membros
    sendCommand('get_members', { room: roomName });

    setIsJoined(true);

    return unsubscribeFunc;
  }, [roomName, subscribe, sendCommand, onMessage, onJoin, onLeave, isJoined]);

  // Sai da sala
  const leaveRoom = useCallback(() => {
    if (!isJoined || !roomName) return;

    const channel = `ws:room:${roomName}`;
    unsubscribe(channel);
    
    // Envia comando para sair da sala
    sendCommand('leave_room', { room: roomName });

    setIsJoined(false);
  }, [roomName, unsubscribe, sendCommand, isJoined]);

  // Envia uma mensagem para a sala
  const sendMessage = useCallback((content: any) => {
    if (!roomName || !isJoined) return;

    const channel = `ws:room:${roomName}`;
    publish(channel, {
      type: 'message',
      content,
    });
  }, [roomName, publish, isJoined]);

  // Auto-entrada
  useEffect(() => {
    if (autoJoin && roomName && !isJoined) {
      const unsubscribeFunc = joinRoom();
      return () => {
        if (unsubscribeFunc) unsubscribeFunc();
        leaveRoom();
      };
    }
    return undefined;
  }, [autoJoin, roomName, isJoined, joinRoom, leaveRoom]);

  return {
    messages,
    members,
    isJoined,
    joinRoom,
    leaveRoom,
    sendMessage,
  };
}