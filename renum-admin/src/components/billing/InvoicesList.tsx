import React from 'react';
import Link from 'next/link';
import { Eye, Download } from 'lucide-react';
import { Invoice } from '../../types/billing';
import { formatCurrency, formatDate } from '../../lib/utils';
import Table from '../ui/Table';

interface InvoicesListProps {
  data: Invoice[];
  isLoading: boolean;
  onDownload?: (invoiceId: string) => void;
}

const InvoicesList: React.FC<InvoicesListProps> = ({ data, isLoading, onDownload }) => {
  const columns = [
    { header: 'Cliente', accessor: (row: Invoice) => row.client_name },
    { header: 'Valor', accessor: (row: Invoice) => formatCurrency(row.amount) },
    { 
      header: 'Status', 
      accessor: (row: Invoice) => {
        const statusClasses = {
          'draft': 'bg-gray-100 text-gray-800',
          'sent': 'bg-blue-100 text-blue-800',
          'paid': 'bg-green-100 text-green-800',
          'overdue': 'bg-red-100 text-red-800',
          'cancelled': 'bg-gray-100 text-gray-800',
        };
        
        const statusLabels = {
          'draft': 'Rascunho',
          'sent': 'Enviada',
          'paid': 'Paga',
          'overdue': 'Atrasada',
          'cancelled': 'Cancelada',
        };
        
        return (
          <span
            className={`px-2 py-1 rounded-full text-xs ${statusClasses[row.status]}`}
          >
            {statusLabels[row.status]}
          </span>
        );
      }
    },
    { header: 'Data de Emissão', accessor: (row: Invoice) => formatDate(row.issue_date) },
    { header: 'Data de Vencimento', accessor: (row: Invoice) => formatDate(row.due_date) },
    { 
      header: 'Período', 
      accessor: (row: Invoice) => `${formatDate(row.period_start)} - ${formatDate(row.period_end)}` 
    },
    {
      header: 'Ações',
      accessor: (row: Invoice) => (
        <div className="flex space-x-2">
          <Link href={`/billing/invoices/${row.id}`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Eye className="h-5 w-5" />
            </a>
          </Link>
          {onDownload && (
            <button
              onClick={() => onDownload(row.id)}
              className="text-blue-600 hover:text-blue-800"
            >
              <Download className="h-5 w-5" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="Nenhuma fatura encontrada"
    />
  );
};

export default InvoicesList;