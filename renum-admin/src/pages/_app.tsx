import '../styles/globals.css';
import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProtectedRoute from '../components/layout/ProtectedRoute';
import Layout from '../components/layout/Layout';

// Criar cliente de consulta
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function MyApp({ Component, pageProps }: AppProps) {
  // Lista de rotas que não precisam de layout (como a página de login)
  const noLayoutRoutes = ['/login'];
  const path = typeof window !== 'undefined' ? window.location.pathname : '';
  const needsLayout = !noLayoutRoutes.includes(path);

  return (
    <QueryClientProvider client={queryClient}>
      <ProtectedRoute>
        {needsLayout ? (
          <Layout>
            <Component {...pageProps} />
          </Layout>
        ) : (
          <Component {...pageProps} />
        )}
      </ProtectedRoute>
    </QueryClientProvider>
  );
}

export default MyApp;