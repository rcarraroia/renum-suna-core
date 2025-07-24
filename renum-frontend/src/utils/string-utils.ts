/**
 * Utilitários para manipulação de strings
 */

/**
 * Trunca uma string para o tamanho máximo especificado e adiciona reticências se necessário
 * @param str String a ser truncada
 * @param maxLength Tamanho máximo da string
 * @returns String truncada
 */
export function truncateString(str: string, maxLength: number): string {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}

/**
 * Formata uma data para exibição
 * @param dateString String de data no formato ISO
 * @param options Opções de formatação
 * @returns Data formatada
 */
export function formatDate(dateString: string, options: Intl.DateTimeFormatOptions = {}): string {
  if (!dateString) return '';
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options
  };
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', defaultOptions).format(date);
  } catch (error) {
    console.error('Erro ao formatar data:', error);
    return dateString;
  }
}

/**
 * Capitaliza a primeira letra de uma string
 * @param str String a ser capitalizada
 * @returns String com a primeira letra maiúscula
 */
export function capitalizeFirstLetter(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Converte um enum em um array de opções para select
 * @param enumObject Objeto enum
 * @returns Array de opções {value, label}
 */
export function enumToOptions(enumObject: Record<string, string>): Array<{value: string, label: string}> {
  return Object.entries(enumObject)
    .filter(([key]) => isNaN(Number(key))) // Filtra chaves numéricas
    .map(([_, value]) => ({
      value,
      label: value.split('_').map(capitalizeFirstLetter).join(' ')
    }));
}

/**
 * Gera um ID único
 * @returns ID único
 */
export function generateUniqueId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

/**
 * Formata um número para exibição com separador de milhares
 * @param num Número a ser formatado
 * @param options Opções de formatação
 * @returns Número formatado
 */
export function formatNumber(num: number, options: Intl.NumberFormatOptions = {}): string {
  if (num === undefined || num === null) return '';
  
  const defaultOptions: Intl.NumberFormatOptions = {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  };
  
  return new Intl.NumberFormat('pt-BR', defaultOptions).format(num);
}

/**
 * Formata um valor monetário para exibição
 * @param value Valor a ser formatado
 * @param currency Moeda (padrão: USD)
 * @returns Valor monetário formatado
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  if (value === undefined || value === null) return '';
  
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}