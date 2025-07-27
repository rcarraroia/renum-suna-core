/**
 * Utilitários para tratamento de erros da API
 */

import { AxiosError } from 'axios';
import { ApiErrorResponse } from './api-types';

/**
 * Classe de erro personalizada para erros da API
 */
export class ApiError extends Error {
  status: number;
  detail?: string;
  errors?: Record<string, string[]>;
  originalError: Error;

  constructor(status: number, message: string, detail?: string, errors?: Record<string, string[]>, originalError?: Error) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.errors = errors;
    this.originalError = originalError || new Error(message);
  }

  /**
   * Cria uma instância de ApiError a partir de um AxiosError
   */
  static fromAxiosError(error: AxiosError<ApiErrorResponse>): ApiError {
    const status = error.response?.status || 500;
    const message = error.response?.data?.message || error.message || 'Erro desconhecido';
    const detail = error.response?.data?.detail;
    const errors = error.response?.data?.errors;

    return new ApiError(status, message, detail, errors, error);
  }

  /**
   * Verifica se o erro é um erro de autenticação (401)
   */
  isAuthError(): boolean {
    return this.status === 401;
  }

  /**
   * Verifica se o erro é um erro de não autorizado (401)
   * Alias para isAuthError para compatibilidade
   */
  isUnauthorized(): boolean {
    return this.isAuthError();
  }

  /**
   * Verifica se o erro é um erro de permissão (403)
   */
  isPermissionError(): boolean {
    return this.status === 403;
  }

  /**
   * Verifica se o erro é um erro de validação (422)
   */
  isValidationError(): boolean {
    return this.status === 422 && !!this.errors;
  }

  /**
   * Verifica se o erro é um erro de servidor (500+)
   */
  isServerError(): boolean {
    return this.status >= 500;
  }

  /**
   * Obtém mensagens de erro de validação para um campo específico
   */
  getFieldErrors(field: string): string[] {
    return this.errors?.[field] || [];
  }

  /**
   * Obtém a primeira mensagem de erro de validação para um campo específico
   */
  getFirstFieldError(field: string): string | undefined {
    return this.getFieldErrors(field)[0];
  }

  /**
   * Obtém uma mensagem amigável para o usuário
   */
  getUserFriendlyMessage(): string {
    if (this.isAuthError()) {
      return 'Sua sessão expirou. Por favor, faça login novamente.';
    }

    if (this.isPermissionError()) {
      return 'Você não tem permissão para realizar esta ação.';
    }

    if (this.isValidationError()) {
      return 'Por favor, verifique os dados informados e tente novamente.';
    }

    if (this.isServerError()) {
      return 'Ocorreu um erro no servidor. Por favor, tente novamente mais tarde.';
    }

    return this.message;
  }
}

/**
 * Função auxiliar para tratar erros da API
 * 
 * @param error - Erro a ser tratado
 * @returns ApiError
 */
export function handleApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (axios.isAxiosError(error) && error.response) {
    return ApiError.fromAxiosError(error);
  }

  // Erro genérico
  const message = error instanceof Error ? error.message : 'Erro desconhecido';
  return new ApiError(500, message, undefined, undefined, error instanceof Error ? error : undefined);
}

/**
 * Hook para tratamento de erros da API
 * 
 * @param error - Erro a ser tratado
 * @returns Objeto com informações sobre o erro
 */
export function useApiErrorHandler() {
  return {
    handleError: (error: unknown): ApiError => {
      const apiError = handleApiError(error);
      
      // Aqui você pode adicionar lógica para exibir notificações, 
      // redirecionar para página de login em caso de erro de autenticação, etc.
      
      return apiError;
    }
  };
}

// Re-exporta axios para uso consistente
import axios from 'axios';
export { axios };