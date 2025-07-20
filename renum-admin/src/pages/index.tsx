import React from 'react';
import Head from 'next/head';
import { Users, Database, Bot, CreditCard, Activity } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import MetricsCard from '../components/dashboard/MetricsCard';
import UsageChart from '../components/dashboard/UsageChart';
import StatusOverview from '../components/dashboard/StatusOverview';
import RecentActivities from '../components/dashboard/RecentActivities';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import ProtectedRoute from '../components/layout/ProtectedRoute';

export default function Dashboard() {
  const { user } = useAuth();

  // Dados de exemplo
  const metrics = [
    { 
      title: 'Total de Clientes', 
      value: 24, 
      change: 12, 
      icon: <Users className="h-6 w-6 text-primary-600" /> 
    },
    { 
      title: 'Total de Agentes', 
      value: 156, 
      change: 8, 
      icon: <Bot className="h-6 w-6 text-primary-600" /> 
    },
    { 
      title: 'Bases de Conhecimento', 
      value: 42, 
      change: 5, 
      icon: <Database className="h-6 w-6 text-primary-600" /> 
    },
    { 
      title: 'Faturamento Mensal', 
      value: 'R$ 12.450', 
      change: 15, 
      icon: <CreditCard className="h-6 w-6 text-primary-600" /> 
    }
  ];

  return (
    <ProtectedRoute>
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
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2 text-primary-600" />
                Uso do Sistema
              </CardTitle>
            </CardHeader>
            <CardContent>
              <UsageChart />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Status dos Serviços</CardTitle>
            </CardHeader>
            <CardContent>
              <StatusOverview />
            </CardContent>
          </Card>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Atividades Recentes</CardTitle>
          </CardHeader>
          <CardContent>
            <RecentActivities />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}