// Contexto de Autenticação

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { apiClient } from '../services/api-client';
import { ApiError } from '../services/api-error';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: ApiError | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);

  // Verifica se o usuário está autenticado ao carregar a aplicação
  const checkAuth = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Verifica se há um token armazenado
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setUser(null);
        setLoading(false);
        return false;
      }
      
      // Configura o token no cliente de API
      apiClient.setToken(token);
      
      // Busca informações do usuário
      const userData = await apiClient.get<User>('/auth/me');
      setUser(userData);
      setLoading(false);
      return true;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      
      // Se for erro de autenticação, limpa o token
      if (apiError.isUnauthorized()) {
        localStorage.removeItem('auth_token');
        apiClient.clearToken();
      }
      
      setError(apiError);
      setUser(null);
      setLoading(false);
      return false;
    }
  }, []);

  // Verifica a autenticação ao iniciar
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Função de login
  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Faz a requisição de login
      const response = await apiClient.post<{ token: string; user: User }>('/auth/login', { email, password });
      
      // Armazena o token e configura o cliente de API
      localStorage.setItem('auth_token', response.token);
      apiClient.setToken(response.token);
      
      // Atualiza o estado com as informações do usuário
      setUser(response.user);
      setLoading(false);
      return true;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setUser(null);
      setLoading(false);
      return false;
    }
  }, []);

  // Função de logout
  const logout = useCallback(() => {
    // Remove o token do armazenamento local
    localStorage.removeItem('auth_token');
    apiClient.clearToken();
    
    // Limpa o estado do usuário
    setUser(null);
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}