/**
 * Utilitários gerais para o frontend
 */

/**
 * Formata uma data para exibição
 * @param dateString - String de data ISO
 * @param options - Opções de formatação (opcional)
 * @returns Data formatada
 */
export function formatDate(dateString: string, options?: Intl.DateTimeFormatOptions): string {
  try {
    const date = new Date(dateString);
    const defaultOptions: Intl.DateTimeFormatOptions = {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    
    return new Intl.DateTimeFormat('pt-BR', options || defaultOptions).format(date);
  } catch (error) {
    console.error('Erro ao formatar data:', error);
    return dateString;
  }
}

/**
 * Trunca um texto para um tamanho máximo
 * @param text - Texto a ser truncado
 * @param maxLength - Tamanho máximo
 * @returns Texto truncado
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
}

/**
 * Gera um ID único
 * @returns ID único
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Formata bytes para uma string legível
 * @param bytes - Número de bytes
 * @param decimals - Número de casas decimais
 * @returns String formatada
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Converte um objeto para parâmetros de URL
 * @param params - Objeto com parâmetros
 * @returns String de parâmetros de URL
 */
export function objectToQueryString(params: Record<string, any>): string {
  return Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null)
    .map(key => {
      if (Array.isArray(params[key])) {
        return params[key]
          .map((value: any) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
          .join('&');
      }
      return `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`;
    })
    .join('&');
}

/**
 * Atrasa a execução por um tempo determinado
 * @param ms - Tempo em milissegundos
 * @returns Promise que resolve após o tempo especificado
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Capitaliza a primeira letra de uma string
 * @param str - String a ser capitalizada
 * @returns String capitalizada
 */
export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Formata um nome de ferramenta para exibição
 * @param toolId - ID da ferramenta
 * @returns Nome formatado
 */
export function formatToolName(toolId: string): string {
  if (!toolId) return '';
  return toolId
    .split('_')
    .map(word => capitalize(word))
    .join(' ');
}

/**
 * Verifica se um objeto está vazio
 * @param obj - Objeto a ser verificado
 * @returns Verdadeiro se o objeto estiver vazio
 */
export function isEmptyObject(obj: Record<string, any>): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Remove propriedades nulas ou indefinidas de um objeto
 * @param obj - Objeto a ser limpo
 * @returns Objeto sem propriedades nulas ou indefinidas
 */
export function removeNullProperties<T>(obj: T): Partial<T> {
  const result: Partial<T> = {};
  
  Object.entries(obj as Record<string, any>).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      (result as Record<string, any>)[key] = value;
    }
  });
  
  return result;
}

/**
 * Retorna a classe CSS para a cor de fundo do status do agente
 * @param status - Status do agente
 * @returns Classe CSS para a cor de fundo
 */
export function getAgentStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
    case 'ativo':
      return 'bg-green-100 text-green-800';
    case 'draft':
    case 'rascunho':
      return 'bg-yellow-100 text-yellow-800';
    case 'inactive':
    case 'inativo':
      return 'bg-gray-100 text-gray-800';
    case 'error':
    case 'erro':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Traduz o status do agente para português
 * @param status - Status do agente em inglês
 * @returns Status traduzido
 */
export function translateAgentStatus(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
      return 'Ativo';
    case 'draft':
      return 'Rascunho';
    case 'inactive':
      return 'Inativo';
    case 'error':
      return 'Erro';
    default:
      return capitalize(status);
  }
}