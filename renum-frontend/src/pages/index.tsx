import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuthStore } from '../lib/store';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Redirecionar para o dashboard se estiver autenticado, ou para o login caso contrário
    if (isAuthenticated) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // Não renderizar nada, apenas redirecionar
  return null;
}