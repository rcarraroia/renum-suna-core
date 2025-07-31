import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft, Download, Printer, Mail } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useBilling } from '../../../hooks/useBilling';
import { Invoice } from '../../../types/billing';
import { formatCurrency, formatDate } from '../../../lib/utils';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import Table from '../../../components/ui/Table';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';
import { InvoiceItem } from '../../../types/billing';

export default function InvoiceDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { getInvoice, error, setError } = useBilling();
  const [invoice, setInvoice] = useState<Invoice | null>(null);

  // Buscar detalhes da fatura
  const {
    data: invoiceData,
    isLoading: isLoadingInvoice,
    error: invoiceError,
  } = useQuery<Invoice>({
    queryKey: ['invoice', id],
    queryFn: () => getInvoice(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (invoiceData) {
      setInvoice(invoiceData);
    }
  }, [invoiceData]);

  useEffect(() => {
    if (invoiceError) {
      setError(invoiceError.message);
    }
  }, [invoiceError, setError]);

  const handleDownload = () => {
    // Implementar download de fatura
    console.log(`Download invoice ${id}`);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleSendEmail = () => {
    // Implementar envio de email
    console.log(`Send invoice ${id} by email`);
  };

  if (isLoadingInvoice) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!invoice && !isLoadingInvoice) {
    return (
      <Alert variant="error" title="Erro">
        Fatura não encontrada
      </Alert>
    );
  }

  const getStatusLabel = (status: string) => {
    const statusLabels: Record<string, string> = {
      'draft': 'Rascunho',
      'sent': 'Enviada',
      'paid': 'Paga',
      'overdue': 'Atrasada',
      'cancelled': 'Cancelada',
    };
    return statusLabels[status] || status;
  };

  const getStatusClass = (status: string) => {
    const statusClasses: Record<string, string> = {
      'draft': 'bg-gray-100 text-gray-800',
      'sent': 'bg-blue-100 text-blue-800',
      'paid': 'bg-green-100 text-green-800',
      'overdue': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800',
    };
    return statusClasses[status] || '';
  };

  const columns = [
    { header: 'Descrição', accessor: (row: InvoiceItem) => row.description },
    { header: 'Quantidade', accessor: (row: InvoiceItem) => row.quantity },
    { header: 'Preço Unitário', accessor: (row: any) => formatCurrency(row.unit_price) },
    { header: 'Total', accessor: (row: any) => formatCurrency(row.amount) },
  ];

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Detalhes da Fatura</title>
        <meta name="description" content="Detalhes da fatura" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/billing/invoices">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Fatura #{invoice?.id.slice(-8)}</h1>
          <div className="ml-auto flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSendEmail}
            >
              <Mail className="h-4 w-4 mr-2" /> Enviar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrint}
            >
              <Printer className="h-4 w-4 mr-2" /> Imprimir
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
            >
              <Download className="h-4 w-4 mr-2" /> Download
            </Button>
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

        <div className="print:bg-white print:p-8">
          <div className="bg-white p-8 rounded-lg shadow mb-6 print:shadow-none">
            <div className="flex justify-between items-start mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Renum AI</h2>
                <p className="text-gray-600">contato@renum.ai</p>
                <p className="text-gray-600">CNPJ: 12.345.678/0001-90</p>
              </div>
              <div className="text-right">
                <h3 className="text-xl font-bold text-gray-900">Fatura #{invoice?.id.slice(-8)}</h3>
                <p className="text-gray-600">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${getStatusClass(invoice?.status || '')}`}
                  >
                    {getStatusLabel(invoice?.status || '')}
                  </span>
                </p>
                <p className="text-gray-600 mt-2">Emitida em: {formatDate(invoice?.issue_date || '')}</p>
                <p className="text-gray-600">Vencimento: {formatDate(invoice?.due_date || '')}</p>
                {invoice?.paid_date && (
                  <p className="text-green-600">Paga em: {formatDate(invoice.paid_date)}</p>
                )}
              </div>
            </div>

            <div className="border-t border-b border-gray-200 py-4 mb-8">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Cliente</h3>
              <p className="text-gray-800">{invoice?.client_name}</p>
              <p className="text-gray-600">ID: {invoice?.client_id}</p>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Período de Faturamento</h3>
              <p className="text-gray-800">
                {formatDate(invoice?.period_start || '')} a {formatDate(invoice?.period_end || '')}
              </p>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Itens</h3>
              <Table
                columns={columns}
                data={invoice?.items || []}
                isLoading={false}
                emptyMessage="Nenhum item na fatura"
              />
            </div>

            <div className="flex justify-end">
              <div className="w-64">
                <div className="flex justify-between py-2 border-t border-gray-200">
                  <span className="font-medium">Subtotal:</span>
                  <span>{formatCurrency(invoice?.amount || 0)}</span>
                </div>
                <div className="flex justify-between py-2 border-t border-gray-200">
                  <span className="font-medium">Impostos:</span>
                  <span>{formatCurrency(0)}</span>
                </div>
                <div className="flex justify-between py-2 border-t border-b border-gray-200 text-lg font-bold">
                  <span>Total:</span>
                  <span>{formatCurrency(invoice?.amount || 0)}</span>
                </div>
              </div>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Informações de Pagamento</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Instruções</h4>
                  <p className="text-sm text-gray-600">
                    Por favor, efetue o pagamento até a data de vencimento. Para dúvidas ou problemas,
                    entre em contato com nossa equipe de suporte em suporte@renum.ai.
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Dados Bancários</h4>
                  <p className="text-sm text-gray-600">
                    Banco: 001 - Banco do Brasil<br />
                    Agência: 1234-5<br />
                    Conta: 12345-6<br />
                    CNPJ: 12.345.678/0001-90<br />
                    Favorecido: Renum AI Tecnologia Ltda.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  );
}