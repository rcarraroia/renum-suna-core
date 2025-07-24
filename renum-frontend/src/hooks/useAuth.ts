// Hooks personalizados para autenticação

import { useState, useCallback } from 'react';
import { useAuthContext } from '../contexts/AuthContext';

// Hook para gerenciar o login
export function useLogin() {
  const { login, loading, error, isAuthenticated } = useAuthContext();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleEmailChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  }, []);

  const handlePasswordChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    return login(email, password);
  }, [email, password, login]);

  const clearForm = useCallback(() => {
    setEmail('');
    setPassword('');
  }, []);

  return {
    email,
    password,
    handleEmailChange,
    handlePasswordChange,
    handleSubmit,
    clearForm,
    loading,
    error,
    isAuthenticated
  };
}

// Hook para gerenciar o logout
export function useLogout() {
  const { logout, isAuthenticated } = useAuthContext();

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  return {
    handleLogout,
    isAuthenticated
  };
}

// Hook para verificar autenticação
export function useAuthCheck() {
  const { checkAuth, isAuthenticated, user, loading } = useAuthContext();

  return {
    checkAuth,
    isAuthenticated,
    user,
    loading
  };
}