import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Download, Filter } from 'lucide-react';
import { useBilling } from '../../hooks/useBilling';
import { useClients } from '../../hooks/useClients';
import { BillingPeriod } from '../../types/billing';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import Modal from '../../components/ui/Modal';
import Select from '../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import UsageChart from '../../components/billing/UsageChart';
import PeriodSelector from '../../components/billing/PeriodSelector';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function Reports() {
  const {
    billingPeriods,
    isLoadingPeriods,
    currentPeriod,
    setCurrentPeriod,
    getUsageReport,
    exportReport,
    isExportingReport,
    error,
    setError,
  } = useBilling();

  const { clients, isLoadingClients } = useClients();

  const [selectedPeriod, setSelectedPeriod] = useState<BillingPeriod | null>(null);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [showTokens, setShowTokens] = useState(true);
  const [showApiCalls, setShowApiCalls] = useState(true);
  const [showStorage, setShowStorage] = useState(true);

  useEffect(() => {
    if (currentPeriod && !selectedPeriod) {
      setSelectedPeriod(currentPeriod);
    }
  }, [currentPeriod, selectedPeriod]);

  const handlePeriodChange = (period: BillingPeriod) => {
    setSelectedPeriod(period);
  };

  const {
    data: usageReportData,
    isLoading: isLoadingUsageReport,
  } = getUsageReport(
    selectedClient || undefined,
    selectedPeriod?.label
  );

  const handleExportReport = (format: 'csv' | 'pdf') => {
    exportReport({
      type: 'usage',
      format,
      period: selectedPeriod?.label,
      clientId: selectedClient || undefined,
    });
  };

  const handleApplyFilters = () => {
    setIsFilterModalOpen(false);
  };

  const handleClearFilters = () => {
    setSelectedClient('');
    setShowTokens(true);
    setShowApiCalls(true);
    setShowStorage(true);
    setIsFilterModalOpen(false);
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Relatórios</title>
        <meta name="description" content="Relatórios de uso e faturamento" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/billing">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>
          <div className="ml-auto flex space-x-3">
            <PeriodSelector
              periods={billingPeriods || []}
              currentPeriod={selectedPeriod}
              onChange={handlePeriodChange}
              isLoading={isLoadingPeriods}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsFilterModalOpen(true)}
            >
              <Filter className="h-4 w-4 mr-2" /> Filtrar
            </Button>
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
          <Card>
            <CardHeader>
              <CardTitle>
                Relatório de Uso
                {selectedClient && clients && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    Cliente: {clients.find(c => c.id === selectedClient)?.name}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <UsageChart
                data={usageReportData!}
                isLoading={isLoadingUsageReport}
                showTokens={showTokens}
                showApiCalls={showApiCalls}
                showStorage={showStorage}
              />
            </CardContent>
          </Card>

          {usageReportData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tokens</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    {usageReportData.totals.tokens.toLocaleString()}
                  </div>
                  <p className="text-sm text-gray-600">
                    Total de tokens consumidos no período
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Chamadas de API</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    {usageReportData.totals.api_calls.toLocaleString()}
                  </div>
                  <p className="text-sm text-gray-600">
                    Total de chamadas de API no período
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Armazenamento</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-gray-900 mb-2">
                    {usageReportData.totals.storage_gb.toLocaleString()} GB
                  </div>
                  <p className="text-sm text-gray-600">
                    Total de armazenamento utilizado
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

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
                    clientId: selectedClient || undefined,
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
                    clientId: selectedClient || undefined,
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
                    clientId: selectedClient || undefined,
                  })}
                  isLoading={isExportingReport}
                >
                  <Download className="h-4 w-4 mr-2" /> Exportar
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        <Modal
          isOpen={isFilterModalOpen}
          onClose={() => setIsFilterModalOpen(false)}
          title="Filtrar Relatório"
        >
          <div className="space-y-4">
            <div>
              <label
                htmlFor="client"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Cliente
              </label>
              <Select
                id="client"
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                options={[
                  { value: '', label: 'Todos os clientes' },
                  ...(clients || []).map((client) => ({
                    value: client.id,
                    label: client.name,
                  })),
                ]}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Métricas a Exibir
              </label>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    id="show_tokens"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    checked={showTokens}
                    onChange={(e) => setShowTokens(e.target.checked)}
                  />
                  <label
                    htmlFor="show_tokens"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Tokens
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="show_api_calls"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    checked={showApiCalls}
                    onChange={(e) => setShowApiCalls(e.target.checked)}
                  />
                  <label
                    htmlFor="show_api_calls"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Chamadas de API
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="show_storage"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    checked={showStorage}
                    onChange={(e) => setShowStorage(e.target.checked)}
                  />
                  <label
                    htmlFor="show_storage"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Armazenamento
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                variant="outline"
                onClick={handleClearFilters}
              >
                Limpar Filtros
              </Button>
              <Button
                onClick={handleApplyFilters}
              >
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}