import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user && router.pathname !== '/login') {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  // Mostrar tela de carregamento enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Se não estiver autenticado e não estiver na página de login, não renderiza nada
  // (será redirecionado pelo useEffect)
  if (!user && router.pathname !== '/login') {
    return null;
  }

  // Se estiver autenticado ou na página de login, renderiza o conteúdo
  return <>{children}</>;
};

export default ProtectedRoute;