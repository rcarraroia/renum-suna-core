import React from 'react';
import Head from 'next/head';
import { Users, Database, Bot, CreditCard, Activity } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/ui/Card';

// Componente MetricsCard
interface MetricsCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
}

const MetricsCard: React.FC<MetricsCardProps> = ({ title, value, change, icon }) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-xs mt-1 ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {change >= 0 ? '+' : ''}{change}% desde o último período
            </p>
          )}
        </div>
        <div className="p-3 bg-primary-100 rounded-full">
          {icon}
        </div>
      </div>
    </Card>
  );
};

// Componente StatusOverview
const StatusOverview: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span>API Renum</span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Operacional</span>
      </div>
      <div className="flex items-center justify-between">
        <span>API Suna</span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Operacional</span>
      </div>
      <div className="flex items-center justify-between">
        <span>Supabase</span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Operacional</span>
      </div>
      <div className="flex items-center justify-between">
        <span>OpenAI</span>
        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">Degradado</span>
      </div>
      <div className="flex items-center justify-between">
        <span>Anthropic</span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Operacional</span>
      </div>
    </div>
  );
};

// Página principal
export default function Home() {
  const { user } = useAuth();

  // Dados de exemplo
  const metrics = [
    { title: 'Total de Clientes', value: 24, change: 12, icon: <Users className="h-6 w-6 text-primary-600" /> },
    { title: 'Total de Agentes', value: 156, change: 8, icon: <Bot className="h-6 w-6 text-primary-600" /> },
    { title: 'Bases de Conhecimento', value: 42, change: 5, icon: <Database className="h-6 w-6 text-primary-600" /> },
    { title: 'Faturamento Mensal', value: 'R$ 12.450', change: 15, icon: <CreditCard className="h-6 w-6 text-primary-600" /> }
  ];

  return (
    <>
      <Head>
        <title>Renum Admin - Dashboard</title>
        <meta name="description" content="Painel administrativo Renum" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Bem-vindo, {user?.name || 'Administrador'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric, index) => (
            <MetricsCard
              key={index}
              title={metric.title}
              value={metric.value}
              change={metric.change}
              icon={metric.icon}
            />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium mb-4 flex items-center">
              <Activity className="h-5 w-5 mr-2 text-primary-600" />
              Uso do Sistema
            </h2>
            <div className="h-64 flex items-center justify-center text-gray-500">
              Gráfico de uso será exibido aqui
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium mb-4">Status dos Serviços</h2>
            <StatusOverview />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium mb-4">Atividades Recentes</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-primary-500 pl-4">
              <p className="text-sm text-gray-600">Há 5 minutos</p>
              <p className="font-medium">Novo cliente registrado: Empresa XYZ</p>
            </div>
            <div className="border-l-4 border-primary-500 pl-4">
              <p className="text-sm text-gray-600">Há 15 minutos</p>
              <p className="font-medium">Agente "Assistente de Vendas" criado por Cliente ABC</p>
            </div>
            <div className="border-l-4 border-primary-500 pl-4">
              <p className="text-sm text-gray-600">Há 1 hora</p>
              <p className="font-medium">Limite de uso atingido para Cliente DEF</p>
            </div>
            <div className="border-l-4 border-primary-500 pl-4">
              <p className="text-sm text-gray-600">Há 3 horas</p>
              <p className="font-medium">Nova base de conhecimento criada: "Documentação Técnica"</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}