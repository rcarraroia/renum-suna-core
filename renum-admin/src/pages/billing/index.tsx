import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Download, Settings, AlertTriangle } from 'lucide-react';
import { useBilling } from '../../hooks/useBilling';
import { BillingPeriod } from '../../types/billing';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import BillingOverviewCards from '../../components/billing/BillingOverviewCards';
import ClientBillingTable from '../../components/billing/ClientBillingTable';
import PeriodSelector from '../../components/billing/PeriodSelector';
import UsageChart from '../../components/billing/UsageChart';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function BillingOverview() {
  const {
    billingPeriods,
    isLoadingPeriods,
    currentPeriod,
    setCurrentPeriod,
    getBillingOverview,
    getClientBilling,
    getUsageReport,
    exportReport,
    isExportingReport,
    error,
    setError,
  } = useBilling();

  const [selectedPeriod, setSelectedPeriod] = useState<BillingPeriod | null>(null);

  useEffect(() => {
    if (currentPeriod && !selectedPeriod) {
      setSelectedPeriod(currentPeriod);
    }
  }, [currentPeriod, selectedPeriod]);

  const handlePeriodChange = (period: BillingPeriod) => {
    setSelectedPeriod(period);
  };

  const {
    data: overviewData,
    isLoading: isLoadingOverview,
  } = getBillingOverview(selectedPeriod?.label);

  const {
    data: clientBillingData,
    isLoading: isLoadingClientBilling,
  } = getClientBilling(selectedPeriod?.label);

  const {
    data: usageReportData,
    isLoading: isLoadingUsageReport,
  } = getUsageReport(undefined, selectedPeriod?.label);

  const handleExportReport = (format: 'csv' | 'pdf') => {
    exportReport({
      type: 'billing',
      format,
      period: selectedPeriod?.label,
    });
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Faturamento</title>
        <meta name="description" content="Visão geral de faturamento" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Faturamento</h1>
            <p className="text-gray-600">Visão geral de faturamento e uso</p>
          </div>
          <div className="flex space-x-3">
            <PeriodSelector
              periods={billingPeriods || []}
              currentPeriod={selectedPeriod}
              onChange={handlePeriodChange}
              isLoading={isLoadingPeriods}
            />
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportReport('csv')}
                isLoading={isExportingReport}
              >
                <Download className="h-4 w-4 mr-2" /> CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportReport('pdf')}
                isLoading={isExportingReport}
              >
                <Download className="h-4 w-4 mr-2" /> PDF
              </Button>
              <Link href="/billing/limits">
                <a>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-2" /> Limites
                  </Button>
                </a>
              </Link>
            </div>
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

        <div className="space-y-6">
          {overviewData && (
            <BillingOverviewCards
              data={overviewData}
              isLoading={isLoadingOverview}
            />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <UsageChart
                data={usageReportData!}
                isLoading={isLoadingUsageReport}
              />
            </div>
            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Alertas de Uso</CardTitle>
                </CardHeader>
                <CardContent>
                  {overviewData && overviewData.total_clients > 0 ? (
                    <div className="space-y-4">
                      {overviewData.total_clients - overviewData.active_clients > 0 && (
                        <div className="flex items-start space-x-3">
                          <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                          <div>
                            <p className="text-sm text-gray-900">
                              <span className="font-medium">
                                {overviewData.total_clients - overviewData.active_clients}
                              </span>{' '}
                              clientes inativos
                            </p>
                            <Link href="/clients?status=inactive">
                              <a className="text-xs text-primary-600 hover:text-primary-800">
                                Ver clientes inativos
                              </a>
                            </Link>
                          </div>
                        </div>
                      )}
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-900">
                            <span className="font-medium">3</span> clientes próximos do limite de uso
                          </p>
                          <Link href="/billing/limits?status=warning">
                            <a className="text-xs text-primary-600 hover:text-primary-800">
                              Ver limites de uso
                            </a>
                          </Link>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-900">
                            <span className="font-medium">1</span> cliente com pagamento atrasado
                          </p>
                          <Link href="/billing/invoices?status=overdue">
                            <a className="text-xs text-primary-600 hover:text-primary-800">
                              Ver faturas atrasadas
                            </a>
                          </Link>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Nenhum alerta disponível</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Faturamento por Cliente</CardTitle>
            </CardHeader>
            <CardContent>
              <ClientBillingTable
                data={clientBillingData || []}
                isLoading={isLoadingClientBilling}
              />
            </CardContent>
          </Card>

          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Relatórios</h2>
            <Link href="/billing/reports">
              <a className="text-primary-600 hover:text-primary-800 text-sm font-medium">
                Ver todos os relatórios
              </a>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Relatório de Uso</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Análise detalhada do uso de recursos por cliente e período
                </p>
                <Button
                  variant="outline"
                  onClick={() => exportReport({
                    type: 'usage',
                    format: 'csv',
                    period: selectedPeriod?.label,
                  })}
                  isLoading={isExportingReport}
                >
                  <Download className="h-4 w-4 mr-2" /> Exportar
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Relatório de Faturamento</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Resumo financeiro com receitas, pagamentos e pendências
                </p>
                <Button
                  variant="outline"
                  onClick={() => exportReport({
                    type: 'billing',
                    format: 'csv',
                    period: selectedPeriod?.label,
                  })}
                  isLoading={isExportingReport}
                >
                  <Download className="h-4 w-4 mr-2" /> Exportar
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Relatório de Faturas</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Lista completa de faturas com status e detalhes de pagamento
                </p>
                <Button
                  variant="outline"
                  onClick={() => exportReport({
                    type: 'invoices',
                    format: 'csv',
                    period: selectedPeriod?.label,
                  })}
                  isLoading={isExportingReport}
                >
                  <Download className="h-4 w-4 mr-2" /> Exportar
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}