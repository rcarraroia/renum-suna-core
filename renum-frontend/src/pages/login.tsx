import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import Image from 'next/image';
import { useForm } from 'react-hook-form';
import { authApi } from '../lib/api-client';
import { useAuthStore } from '../lib/store';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Alert from '../components/ui/Alert';

interface LoginFormData {
  email: string;
  password: string;
}

export default function Login() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debug, setDebug] = useState<string | null>(null);
  const setAuth = useAuthStore((state) => state.setAuth);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Verificar se o usuário já está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  // Verificar se há um erro de autenticação na URL
  useEffect(() => {
    const { error: errorParam } = router.query;
    if (errorParam) {
      setError(Array.isArray(errorParam) ? errorParam[0] : errorParam);
    }
  }, [router.query]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);
    setDebug(null);

    try {
      // Tentar fazer login usando a API real
      try {
        const response = await authApi.login(data.email, data.password);
        
        // Armazenar dados de autenticação
        setAuth(response.user, response.token);
        
        // Verificar se o token foi armazenado corretamente
        const storedToken = localStorage.getItem('token');
        if (!storedToken) {
          setDebug('Aviso: Token não foi armazenado no localStorage. Isso pode causar problemas de autenticação.');
        }
        
        // Redirecionar para o dashboard
        router.push('/dashboard');
        return;
      } catch (apiError: any) {
        console.warn('Falha ao fazer login via API:', apiError);
        
        // Se o erro for específico de credenciais inválidas, mostrar o erro
        if (apiError.message?.includes('credenciais') || 
            apiError.message?.includes('credentials') || 
            apiError.message?.includes('inválido') || 
            apiError.message?.includes('invalid')) {
          throw apiError;
        }
        
        // Se for um erro de conexão, tentar o modo de desenvolvimento
        setDebug(`Tentando modo de desenvolvimento após erro: ${apiError.message}`);
      }
      
      // Simulação de login para desenvolvimento
      if (data.email === 'demo@renum.com' && data.password === 'password') {
        // Simular resposta da API
        const mockUser = {
          id: '1',
          name: 'Usuário Demo',
          email: data.email,
          role: 'user'
        };
        const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6IlVzdcOhcmlvIERlbW8iLCJpYXQiOjE2MTYxNjI4MDB9';
        
        // Simular delay de rede
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Armazenar dados de autenticação
        setAuth(mockUser, mockToken);
        
        // Verificar se o token foi armazenado corretamente
        const storedToken = localStorage.getItem('token');
        if (!storedToken) {
          setDebug('Aviso: Token não foi armazenado no localStorage. Isso pode causar problemas de autenticação.');
        }
        
        // Redirecionar para o dashboard
        router.push('/dashboard');
      } else {
        throw new Error('Email ou senha incorretos');
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao fazer login. Verifique suas credenciais.');
      console.error('Erro ao fazer login:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Head>
        <title>Login | Renum</title>
        <meta name="description" content="Faça login na plataforma Renum" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Image
            src="/images/logo-renum.png"
            alt="Logo Renum"
            width={64}
            height={64}
            className="mx-auto"
          />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Entre na sua conta
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Ou{' '}
          <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
            crie uma nova conta
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <Alert variant="error" className="mb-4">
              {error}
            </Alert>
          )}

          {debug && (
            <Alert variant="info" className="mb-4">
              {debug}
            </Alert>
          )}

          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <Input
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              fullWidth
              error={errors.email?.message}
              {...register('email', {
                required: 'Email é obrigatório',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Email inválido',
                },
              })}
            />

            <Input
              id="password"
              label="Senha"
              type="password"
              autoComplete="current-password"
              fullWidth
              error={errors.password?.message}
              {...register('password', {
                required: 'Senha é obrigatória',
                minLength: {
                  value: 6,
                  message: 'A senha deve ter pelo menos 6 caracteres',
                },
              })}
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Lembrar-me
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
                  Esqueceu sua senha?
                </a>
              </div>
            </div>

            <div>
              <Button
                type="submit"
                fullWidth
                isLoading={isLoading}
                disabled={isLoading}
              >
                Entrar
              </Button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Ou continue com
                </span>
              </div>
            </div>

            <div className="mt-6">
              <Button
                type="button"
                fullWidth
                variant="outline"
                onClick={() => {
                  setError(null);
                  onSubmit({ email: 'demo@renum.com', password: 'password' });
                }}
              >
                Conta de demonstração
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}