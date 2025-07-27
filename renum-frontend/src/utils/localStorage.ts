/**
 * Utility para gerenciar localStorage de forma segura
 */

export class LocalStorageManager {
  /**
   * Verifica se localStorage está disponível
   */
  static isAvailable(): boolean {
    try {
      if (typeof window === 'undefined') return false;
      localStorage.setItem('test', 'test');
      localStorage.removeItem('test');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Obtém o token de autenticação
   */
  static getToken(): string | null {
    return this.isAvailable() ? localStorage.getItem('token') : null;
  }

  /**
   * Define o token de autenticação
   */
  static setToken(token: string): void {
    if (this.isAvailable()) {
      localStorage.setItem('token', token);
    }
  }

  /**
   * Remove o token de autenticação
   */
  static removeToken(): void {
    if (this.isAvailable()) {
      localStorage.removeItem('token');
    }
  }

  /**
   * Obtém um item do localStorage
   */
  static getItem(key: string): string | null {
    return this.isAvailable() ? localStorage.getItem(key) : null;
  }

  /**
   * Define um item no localStorage
   */
  static setItem(key: string, value: string): void {
    if (this.isAvailable()) {
      localStorage.setItem(key, value);
    }
  }

  /**
   * Remove um item do localStorage
   */
  static removeItem(key: string): void {
    if (this.isAvailable()) {
      localStorage.removeItem(key);
    }
  }
}