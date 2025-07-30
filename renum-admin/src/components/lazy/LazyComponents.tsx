import React, { lazy, Suspense } from 'react';

// Loading fallback component
const LoadingFallback = ({ height = 'h-64', message = 'Carregando...' }: { height?: string; message?: string }) => (
  <div className={`animate-pulse bg-gray-200 ${height} rounded-lg flex items-center justify-center`}>
    <div className="text-gray-500 text-sm">{message}</div>
  </div>
);

// Utility function to create lazy components with proper error handling
const createLazyComponent = (importFn: () => Promise<any>, fallback: React.ReactNode, displayName?: string) => {
  const LazyComponent = lazy(importFn);
  
  const WrappedComponent = (props: any) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
  
  WrappedComponent.displayName = displayName || 'LazyComponent';
  
  return WrappedComponent;
};

// Lazy load chart components (pesados e não sempre necessários)
export const LazyUsageChart = createLazyComponent(
  () => import('../billing/UsageChart').catch(() => ({ default: () => <div>Chart não disponível</div> })),
  <LoadingFallback height="h-48" message="Carregando gráfico de uso..." />,
  'LazyUsageChart'
);

// Lazy load settings components (não críticos para operação básica)
export const LazyIntegrationForm = createLazyComponent(
  () => import('../settings/IntegrationForm'),
  <LoadingFallback height="h-96" message="Carregando formulário de integração..." />,
  'LazyIntegrationForm'
);

export const LazyChangeLogList = createLazyComponent(
  () => import('../settings/ChangeLogList'),
  <LoadingFallback height="h-64" message="Carregando changelog..." />,
  'LazyChangeLogList'
);

export const LazySettingForm = createLazyComponent(
  () => import('../settings/SettingForm'),
  <LoadingFallback height="h-80" message="Carregando configurações..." />,
  'LazySettingForm'
);

// Lazy load audit components (carregados sob demanda)
export const LazyAuditLogTable = createLazyComponent(
  () => import('../audit/AuditLogTable'),
  <LoadingFallback height="h-64" message="Carregando logs de auditoria..." />,
  'LazyAuditLogTable'
);

export const LazyAlertRuleForm = createLazyComponent(
  () => import('../audit/AlertRuleForm'),
  <LoadingFallback height="h-96" message="Carregando regras de alerta..." />,
  'LazyAlertRuleForm'
);

// Lazy load user management components
export const LazyUserForm = createLazyComponent(
  () => import('../users/UserForm'),
  <LoadingFallback height="h-80" message="Carregando formulário de usuário..." />,
  'LazyUserForm'
);

export const LazyClientForm = createLazyComponent(
  () => import('../clients/ClientForm'),
  <LoadingFallback height="h-96" message="Carregando formulário de cliente..." />,
  'LazyClientForm'
);

// Lazy load agent management components
export const LazyAgentForm = createLazyComponent(
  () => import('../agents/AgentForm'),
  <LoadingFallback height="h-96" message="Carregando formulário de agente..." />,
  'LazyAgentForm'
);

// Lazy load credential components (sensíveis, carregados sob demanda)
export const LazyCredentialForm = createLazyComponent(
  () => import('../credentials/CredentialForm'),
  <LoadingFallback height="h-80" message="Carregando credenciais..." />,
  'LazyCredentialForm'
);

export const LazyCredentialViewer = createLazyComponent(
  () => import('../credentials/CredentialViewer'),
  <LoadingFallback height="h-48" message="Carregando visualizador..." />,
  'LazyCredentialViewer'
);

// Lazy load homepage components
export const LazyPhraseForm = createLazyComponent(
  () => import('../homepage/PhraseForm'),
  <LoadingFallback height="h-64" message="Carregando editor de frases..." />,
  'LazyPhraseForm'
);

export const LazyTypewriterPreview = createLazyComponent(
  () => import('../homepage/TypewriterPreview'),
  <LoadingFallback height="h-32" message="Carregando preview..." />,
  'LazyTypewriterPreview'
);