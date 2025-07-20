import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'superadmin';
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      // Verificar se o usuário está autenticado
      if (!user) {
        router.push('/login');
        return;
      }

      // Verificar se o usuário está ativo
      if (!user.is_active) {
        router.push('/login');
        return;
      }

      // Verificar se o usuário tem o papel necessário
      if (requiredRole && user.role !== requiredRole && !(requiredRole === 'admin' && user.role === 'superadmin')) {
        router.push('/unauthorized');
        return;
      }
    }
  }, [user, isLoading, router, requiredRole]);

  // Mostrar tela de carregamento enquanto verifica a autenticação
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Se não estiver autenticado ou não tiver permissão, não renderiza nada
  if (!user || !user.is_active || (requiredRole && user.role !== requiredRole && !(requiredRole === 'admin' && user.role === 'superadmin'))) {
    return null;
  }

  // Se estiver autenticado e tiver permissão, renderiza os filhos
  return <>{children}</>;
};

export default ProtectedRoute;