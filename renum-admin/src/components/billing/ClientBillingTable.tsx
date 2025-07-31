import React from 'react';
import Link from 'next/link';
import { Eye } from 'lucide-react';
import { ClientBilling } from '../../types/billing';
import { formatCurrency, formatDate } from '../../lib/utils';
import Table from '../ui/Table';

interface ClientBillingTableProps {
  data: ClientBilling[];
  isLoading: boolean;
}

const ClientBillingTable: React.FC<ClientBillingTableProps> = ({ data, isLoading }) => {
  const columns = [
    { header: 'Cliente', accessor: (row: ClientBilling) => row.client_name },
    { header: 'Plano', accessor: (row: ClientBilling) => {
      const planLabels: Record<string, string> = {
        'basic': 'Básico',
        'standard': 'Padrão',
        'premium': 'Premium',
        'enterprise': 'Enterprise',
      };
      return planLabels[row.plan_type] || row.plan_type;
    }},
    { header: 'Receita', accessor: (row: ClientBilling) => formatCurrency(row.revenue) },
    { header: 'Tokens', accessor: (row: ClientBilling) => row.tokens_used.toLocaleString() },
    { header: 'Chamadas API', accessor: (row: ClientBilling) => row.api_calls.toLocaleString() },
    { 
      header: 'Status', 
      accessor: (row: ClientBilling) => {
        const statusClasses = {
          'paid': 'bg-green-100 text-green-800',
          'pending': 'bg-yellow-100 text-yellow-800',
          'overdue': 'bg-red-100 text-red-800',
          'failed': 'bg-red-100 text-red-800',
        };
        
        const statusLabels = {
          'paid': 'Pago',
          'pending': 'Pendente',
          'overdue': 'Atrasado',
          'failed': 'Falhou',
        };
        
        return (
          <span
            className={`px-2 py-1 rounded-full text-xs ${statusClasses[row.payment_status]}`}
          >
            {statusLabels[row.payment_status]}
          </span>
        );
      }
    },
    { header: 'Próxima Fatura', accessor: (row: ClientBilling) => formatDate(row.next_invoice_date) },
    {
      header: 'Ações',
      accessor: (row: ClientBilling) => (
        <div className="flex space-x-2">
          <Link href={`/billing/clients/${row.client_id}`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Eye className="h-5 w-5" />
            </a>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="Nenhum cliente encontrado"
    />
  );
};

export default ClientBillingTable;