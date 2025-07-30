import React from 'react';
import { ChangeLog } from '../../types/settings';
import { formatDate } from '../../lib/utils';
import Table from '../ui/Table';

interface ChangeLogListProps {
  data: ChangeLog[];
  isLoading: boolean;
}

const ChangeLogList: React.FC<ChangeLogListProps> = ({ data, isLoading }) => {
  const formatValue = (value: any) => {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const columns = [
    { header: 'Configuração', accessor: (row: ChangeLog) => row.setting_key },
    { 
      header: 'Valor Anterior', 
      accessor: (row: ChangeLog) => {
        const value = formatValue(row.old_value);
        return value.length > 50 ? `${value.substring(0, 50)}...` : value;
      }
    },
    { 
      header: 'Novo Valor', 
      accessor: (row: ChangeLog) => {
        const value = formatValue(row.new_value);
        return value.length > 50 ? `${value.substring(0, 50)}...` : value;
      }
    },
    { header: 'Alterado Por', accessor: (row: ChangeLog) => row.changed_by_name },
    { header: 'Data', accessor: (row: ChangeLog) => formatDate(row.changed_at) },
  ];

  return (
    <Table
      columns={columns}
      data={data}
      isLoading={isLoading}
      emptyMessage="Nenhuma alteração encontrada"
    />
  );
};

export default ChangeLogList;