import React, { useEffect } from 'react';
import type { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { useAuthStore } from '../lib/store';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  // Verificar autenticação em rotas protegidas
  useEffect(() => {
    // Lista de rotas públicas que não requerem autenticação
    const publicRoutes = ['/', '/login', '/register'];
    
    // Verificar se a rota atual é protegida
    const isProtectedRoute = !publicRoutes.includes(router.pathname);
    
    // Redirecionar para login se a rota for protegida e o usuário não estiver autenticado
    if (isProtectedRoute && !isAuthenticated) {
      router.push('/login');
    }
  }, [router.pathname, isAuthenticated, router]);

  // Verificar se o token está armazenado corretamente
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        // Verificar se o localStorage está funcionando
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        
        // Verificar se o token está armazenado
        const token = localStorage.getItem('token');
        
        // Se o usuário estiver autenticado mas não houver token, tentar recuperar do estado
        if (isAuthenticated && !token && user) {
          console.warn('Token não encontrado no localStorage, tentando recuperar do estado');
          // Tentar recuperar o token do estado (não é ideal, mas é um fallback)
          const authState = useAuthStore.getState();
          if (authState.token) {
            localStorage.setItem('token', authState.token);
          }
        }
      } catch (error) {
        console.error('Erro ao acessar localStorage:', error);
      }
    }
  }, [isAuthenticated, user]);

  return <Component {...pageProps} />;
}