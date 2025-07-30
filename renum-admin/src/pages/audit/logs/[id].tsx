import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAudit } from '../../../hooks/useAudit';
import { AuditLog } from '../../../types/audit';
import { formatDate } from '../../../lib/utils';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function AuditLogDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { getAuditLog, error, setError } = useAudit();
  const [auditLog, setAuditLog] = useState<AuditLog | null>(null);

  // Buscar detalhes do log de auditoria
  const {
    data: logData,
    isLoading: isLoadingLog,
    error: logError,
  } = useQuery<AuditLog>({
    queryKey: ['audit-log', id],
    queryFn: () => getAuditLog(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (logData) {
      setAuditLog(logData);
    }
  }, [logData]);

  useEffect(() => {
    if (logError) {
      setError(logError.message);
    }
  }, [logError, setError]);

  if (isLoadingLog) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!auditLog && !isLoadingLog) {
    return (
      <Alert variant="error" title="Erro">
        Log de auditoria não encontrado
      </Alert>
    );
  }

  const getActorTypeLabel = (type: string) => {
    const actorTypeLabels: Record<string, string> = {
      'user': 'Usuário',
      'admin': 'Administrador',
      'system': 'Sistema',
    };
    return actorTypeLabels[type] || type;
  };

  const formatJson = (obj: any) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      return String(obj);
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Detalhes do Log de Auditoria</title>
        <meta name="description" content="Detalhes do log de auditoria" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/audit/logs">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Log de Auditoria: {auditLog?.event_type}
          </h1>
        </div>

        {error && (
          <Alert
            variant="error"
            title="Erro"
            onClose={() => setError(null)}
            className="mb-4"
          >
            {error}
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Informações do Evento</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">ID</dt>
                  <dd className="mt-1 text-sm text-gray-900">{auditLog?.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Tipo de Evento</dt>
                  <dd className="mt-1 text-sm text-gray-900">{auditLog?.event_type}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Tipo de Entidade</dt>
                  <dd className="mt-1 text-sm text-gray-900">{auditLog?.entity_type}</dd>
                </div>
                {auditLog?.entity_id && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ID da Entidade</dt>
                    <dd className="mt-1 text-sm text-gray-900">{auditLog.entity_id}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm font-medium text-gray-500">Data e Hora</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {formatDate(auditLog?.created_at || '')}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Informações do Ator</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Tipo de Ator</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {getActorTypeLabel(auditLog?.actor_type || '')}
                  </dd>
                </div>
                {auditLog?.actor_id && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">ID do Ator</dt>
                    <dd className="mt-1 text-sm text-gray-900">{auditLog.actor_id}</dd>
                  </div>
                )}
                {auditLog?.actor_name && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Nome do Ator</dt>
                    <dd className="mt-1 text-sm text-gray-900">{auditLog.actor_name}</dd>
                  </div>
                )}
                {auditLog?.ip_address && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Endereço IP</dt>
                    <dd className="mt-1 text-sm text-gray-900">{auditLog.ip_address}</dd>
                  </div>
                )}
                {auditLog?.user_agent && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">User Agent</dt>
                    <dd className="mt-1 text-sm text-gray-900">{auditLog.user_agent}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Detalhes do Evento</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-50 p-4 rounded-md border border-gray-200 overflow-auto text-sm">
              {formatJson(auditLog?.details || {})}
            </pre>
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}