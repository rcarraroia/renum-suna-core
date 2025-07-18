import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combina classes CSS usando clsx e tailwind-merge
 * @param inputs - Classes CSS a serem combinadas
 * @returns String de classes CSS combinadas
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formata uma data para exibição
 * @param dateString - String de data ISO
 * @param options - Opções de formatação
 * @returns Data formatada
 */
export function formatDate(
  dateString: string,
  options: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }
) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('pt-BR', options).format(date);
}

/**
 * Trunca um texto para um tamanho máximo
 * @param text - Texto a ser truncado
 * @param maxLength - Tamanho máximo
 * @returns Texto truncado
 */
export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

/**
 * Gera um ID único
 * @returns ID único
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Traduz o status de um agente
 * @param status - Status em inglês
 * @returns Status traduzido
 */
export function translateAgentStatus(status: string) {
  const statusMap: Record<string, string> = {
    active: 'Ativo',
    draft: 'Rascunho',
    inactive: 'Inativo',
    archived: 'Arquivado',
  };
  
  return statusMap[status] || status;
}

/**
 * Obtém a cor do status de um agente
 * @param status - Status do agente
 * @returns Classes CSS para a cor do status
 */
export function getAgentStatusColor(status: string) {
  const colorMap: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    draft: 'bg-yellow-100 text-yellow-800',
    inactive: 'bg-gray-100 text-gray-800',
    archived: 'bg-red-100 text-red-800',
  };
  
  return colorMap[status] || 'bg-gray-100 text-gray-800';
}