import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Download, Bell } from 'lucide-react';
import { useAudit } from '../../../hooks/useAudit';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import AuditLogFilter from '../../../components/audit/AuditLogFilter';
import AuditLogTable from '../../../components/audit/AuditLogTable';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function AuditLogs() {
  const {
    auditLogs,
    isLoadingAuditLogs,
    filter,
    setFilter,
    exportAuditLogs,
    isExportingAuditLogs,
    eventTypes,
    isLoadingEventTypes,
    entityTypes,
    isLoadingEntityTypes,
    error,
    setError,
  } = useAudit();

  const handleExportLogs = (format: 'csv' | 'pdf') => {
    exportAuditLogs({
      format,
      filter,
    });
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Logs de Auditoria</title>
        <meta name="description" content="Logs de auditoria do sistema" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Logs de Auditoria</h1>
            <p className="text-gray-600">Monitoramento de atividades do sistema</p>
          </div>
          <div className="flex space-x-3">
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportLogs('csv')}
                isLoading={isExportingAuditLogs}
              >
                <Download className="h-4 w-4 mr-2" /> CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportLogs('pdf')}
                isLoading={isExportingAuditLogs}
              >
                <Download className="h-4 w-4 mr-2" /> PDF
              </Button>
            </div>
            <Link href="/audit/alerts">
              <a>
                <Button variant="outline" size="sm">
                  <Bell className="h-4 w-4 mr-2" /> Alertas
                </Button>
              </a>
            </Link>
          </div>
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

        <AuditLogFilter
          filter={filter}
          onFilterChange={setFilter}
          eventTypes={eventTypes || []}
          entityTypes={entityTypes || []}
          isLoading={isLoadingEventTypes || isLoadingEntityTypes}
        />

        <Card>
          <CardHeader>
            <CardTitle>Logs de Auditoria</CardTitle>
          </CardHeader>
          <CardContent>
            <AuditLogTable
              data={auditLogs || []}
              isLoading={isLoadingAuditLogs}
            />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}