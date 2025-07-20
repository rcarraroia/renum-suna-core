import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import Image from 'next/image';
import { useAuthStore } from '../lib/store';
import TypewriterEffect from '../components/TypewriterEffect';
import { useTypewriterPhrases } from '../hooks/useTypewriterPhrases';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { phrases, isLoading } = useTypewriterPhrases();

  // Redirecionar para o dashboard se estiver autenticado
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  // Frases padrão caso não consiga carregar do banco de dados
  const defaultPhrases = [
    'Crie agentes de IA personalizados para seu negócio',
    'Automatize tarefas repetitivas com inteligência artificial',
    'Conecte seus dados e conhecimento aos modelos de IA mais avançados',
    'Transforme a experiência dos seus clientes com atendimento inteligente',
    'Potencialize sua produtividade com assistentes de IA especializados'
  ];

  // Usar frases do banco de dados ou as padrão
  const displayPhrases = phrases.length > 0 
    ? phrases.map(phrase => phrase.text) 
    : defaultPhrases;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <Head>
        <title>Renum AI - Plataforma de Agentes de IA</title>
        <meta name="description" content="Crie e gerencie agentes de IA personalizados para seu negócio com a plataforma Renum AI" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <Image
              src="/images/logo-renum.png"
              alt="Logo Renum"
              width={40}
              height={40}
            />
            <span className="ml-2 text-xl font-semibold text-gray-900">Renum AI</span>
          </div>
          <div>
            <Link href="/login" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
              Entrar
            </Link>
          </div>
        </div>
      </header>

      <main>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
              <span className="block">Renum AI</span>
            </h1>
            
            {/* Typewriter effect */}
            <div className="mt-3 max-w-md mx-auto">
              <TypewriterEffect 
                phrases={displayPhrases} 
                typingSpeed={80}
                deletingSpeed={40}
                delayBetweenPhrases={2000}
              />
            </div>
            
            <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
              Crie, personalize e implemente agentes de IA para transformar seu negócio.
            </p>
            
            <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
              <div className="rounded-md shadow">
                <Link href="/register" className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10">
                  Começar agora
                </Link>
              </div>
              <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
                <Link href="/about" className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10">
                  Saiba mais
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Features section */}
        <div className="py-12 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="lg:text-center">
              <h2 className="text-base text-indigo-600 font-semibold tracking-wide uppercase">Recursos</h2>
              <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                Uma plataforma completa para seus agentes de IA
              </p>
              <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
                Crie, personalize e implemente agentes de IA para transformar seu negócio.
              </p>
            </div>

            <div className="mt-10">
              <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-3">
                <div className="p-6 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900">Agentes Personalizados</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Crie agentes de IA adaptados às necessidades específicas do seu negócio.
                  </p>
                </div>
                <div className="p-6 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900">Integração de Conhecimento</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Conecte seus dados e documentos para criar agentes com conhecimento especializado.
                  </p>
                </div>
                <div className="p-6 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900">Implantação Multicanal</h3>
                  <p className="mt-2 text-base text-gray-500">
                    Disponibilize seus agentes em múltiplas plataformas e canais de comunicação.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-gray-800">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center">
            <Image
              src="/images/logo-renum-white.png"
              alt="Logo Renum"
              width={40}
              height={40}
            />
          </div>
          <p className="mt-8 text-center text-base text-gray-400">
            &copy; {new Date().getFullYear()} Renum AI. Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}