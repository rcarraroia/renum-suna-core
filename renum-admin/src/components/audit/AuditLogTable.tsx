import React from 'react';
import Link from 'next/link';
import { Eye } from 'lucide-react';
import { AuditLog } from '../../types/audit';
import { formatDate } from '../../lib/utils';
import Table from '../ui/Table';

interface AuditLogTableProps {
  data: AuditLog[];
  isLoading: boolean;
}

const AuditLogTable: React.FC<AuditLogTableProps> = ({ data, isLoading }) => {
  const columns = [
    { header: 'Evento', accessor: (row: AuditLog) => row.event_type },
    { header: 'Entidade', accessor: (row: AuditLog) => `${row.entity_type}${row.entity_id ? ` (${row.entity_id.slice(-8)})` : ''}` },
    { 
      header: 'Ator', 
      accessor: (row: AuditLog) => {
        const actorTypeLabels: Record<string, string> = {
          'user': 'Usuário',
          'admin': 'Admin',
          'system': 'Sistema',
        };
        
        return `${actorTypeLabels[row.actor_type] || row.actor_type}${row.actor_name ? `: ${row.actor_name}` : ''}`;
      }
    },
    { header: 'IP', accessor: (row: AuditLog) => row.ip_address },
    { header: 'Data', accessor: (row: AuditLog) => formatDate(row.created_at) },
    {
      header: 'Ações',
      accessor: (row: AuditLog) => (
        <div className="flex space-x-2">
          <Link href={`/audit/logs/${row.id}`}>
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
      emptyMessage="Nenhum log de auditoria encontrado"
    />
  );
};

export default AuditLogTable;