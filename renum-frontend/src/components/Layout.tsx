import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Sidebar from './Sidebar';
import { useAuthStore } from '../lib/store';

interface LayoutProps {
  children: ReactNode;
  title?: string;
  requireAuth?: boolean;
}

/**
 * Layout principal da aplicação
 */
const Layout = ({ children, title = 'Renum', requireAuth = true }: LayoutProps) => {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // Verificar autenticação
  useEffect(() => {
    if (requireAuth && !isAuthenticated) {
      router.push('/login');
    }
  }, [requireAuth, isAuthenticated, router]);

  // Se a página requer autenticação e o usuário não está autenticado, não renderizar nada
  if (requireAuth && !isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Head>
        <title>{title} | Renum</title>
        <meta name="description" content="Plataforma Renum" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {requireAuth && <Sidebar />}

      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
};

export default Layout;