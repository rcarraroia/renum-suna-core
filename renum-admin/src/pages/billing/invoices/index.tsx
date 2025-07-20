import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Download, Filter } from 'lucide-react';
import { useBilling } from '../../../hooks/useBilling';
import { useClients } from '../../../hooks/useClients';
import { BillingPeriod } from '../../../types/billing';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import Select from '../../../components/ui/Select';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import InvoicesList from '../../../components/billing/InvoicesList';
import PeriodSelector from '../../../components/billing/PeriodSelector';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function Invoices() {
  const {
    billingPeriods,
    isLoadingPeriods,
    currentPeriod,
    setCurrentPeriod,
    getInvoices,
    exportReport,
    isExportingReport,
    error,
    setError,
  } = useBilling();

  const { clients, isLoadingClients } = useClients();

  const [selectedPeriod, setSelectedPeriod] = useState<BillingPeriod | null>(null);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);

  useEffect(() => {
    if (currentPeriod && !selectedPeriod) {
      setSelectedPeriod(currentPeriod);
    }
  }, [currentPeriod, selectedPeriod]);

  const handlePeriodChange = (period: BillingPeriod) => {
    setSelectedPeriod(period);
  };

  const {
    data: invoicesData,
    isLoading: isLoadingInvoices,
  } = getInvoices(
    selectedClient || undefined,
    selectedStatus || undefined,
    selectedPeriod?.label
  );

  const handleExportInvoices = (format: 'csv' | 'pdf') => {
    exportReport({
      type: 'invoices',
      format,
      period: selectedPeriod?.label,
      clientId: selectedClient || undefined,
    });
  };

  const handleDownloadInvoice = (invoiceId: string) => {
    // Implementar download de fatura individual
    console.log(`Download invoice ${invoiceId}`);
  };

  const handleApplyFilters = () => {
    setIsFilterModalOpen(false);
  };

  const handleClearFilters = () => {
    setSelectedClient('');
    setSelectedStatus('');
    setIsFilterModalOpen(false);
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Faturas</title>
        <meta name="description" content="Gerenciamento de faturas" />
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
          <h1 className="text-2xl font-bold text-gray-900">Faturas</h1>
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
                onClick={() => handleExportInvoices('csv')}
                isLoading={isExportingReport}
              >
                <Download className="h-4 w-4 mr-2" /> CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportInvoices('pdf')}
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

        <Card>
          <CardHeader>
            <CardTitle>
              Lista de Faturas
              {selectedClient && clients && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  Cliente: {clients.find(c => c.id === selectedClient)?.name}
                </span>
              )}
              {selectedStatus && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  Status: {
                    {
                      'draft': 'Rascunho',
                      'sent': 'Enviada',
                      'paid': 'Paga',
                      'overdue': 'Atrasada',
                      'cancelled': 'Cancelada',
                    }[selectedStatus]
                  }
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <InvoicesList
              data={invoicesData || []}
              isLoading={isLoadingInvoices}
              onDownload={handleDownloadInvoice}
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFilterModalOpen}
          onClose={() => setIsFilterModalOpen(false)}
          title="Filtrar Faturas"
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
              <label
                htmlFor="status"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Status
              </label>
              <Select
                id="status"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                options={[
                  { value: '', label: 'Todos os status' },
                  { value: 'draft', label: 'Rascunho' },
                  { value: 'sent', label: 'Enviada' },
                  { value: 'paid', label: 'Paga' },
                  { value: 'overdue', label: 'Atrasada' },
                  { value: 'cancelled', label: 'Cancelada' },
                ]}
              />
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