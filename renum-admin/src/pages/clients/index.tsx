import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, Search, Filter, Edit, Trash2, Eye } from 'lucide-react';
import { useClients } from '../../hooks/useClients';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import { formatDate } from '../../lib/utils';
import { Client } from '../../types/client';

export default function ClientsPage() {
  const {
    clients,
    total,
    page,
    pageSize,
    totalPages,
    isLoading,
    setPage,
    setPageSize,
    setSearch,
    setSortBy,
    setSortOrder,
    setFilter,
    deactivateClient,
  } = useClients();

  const [searchQuery, setSearchQuery] = useState('');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchQuery);
    setPage(1);
  };

  const handleDelete = async () => {
    if (selectedClientId) {
      await deactivateClient.mutateAsync(selectedClientId);
      setIsDeleteModalOpen(false);
      setSelectedClientId(null);
    }
  };

  const columns = [
    { header: 'Nome', accessor: (row: Client) => row.name },
    { header: 'Email', accessor: (row: Client) => row.email },
    { 
      header: 'Plano', 
      accessor: (client: any) => {
        const planLabels: Record<string, string> = {
          basic: 'Básico',
          standard: 'Padrão',
          premium: 'Premium',
          enterprise: 'Enterprise',
        };
        return planLabels[client.plan] || client.plan;
      }
    },
    { 
      header: 'Status', 
      accessor: (client: any) => {
        const statusClasses: Record<string, string> = {
          active: 'bg-green-100 text-green-800',
          inactive: 'bg-red-100 text-red-800',
          pending: 'bg-yellow-100 text-yellow-800',
        };
        const statusLabels: Record<string, string> = {
          active: 'Ativo',
          inactive: 'Inativo',
          pending: 'Pendente',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs ${statusClasses[client.status]}`}>
            {statusLabels[client.status] || client.status}
          </span>
        );
      }
    },
    { 
      header: 'Uso', 
      accessor: (client: any) => {
        if (!client.usage_limit) return 'N/A';
        const percentage = Math.round((client.current_usage / client.usage_limit) * 100);
        let bgColor = 'bg-green-500';
        if (percentage > 90) bgColor = 'bg-red-500';
        else if (percentage > 70) bgColor = 'bg-yellow-500';
        
        return (
          <div className="flex items-center">
            <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
              <div className={`${bgColor} h-2.5 rounded-full`} style={{ width: `${percentage}%` }}></div>
            </div>
            <span className="text-xs">{percentage}%</span>
          </div>
        );
      }
    },
    { header: 'Criado em', accessor: (client: any) => formatDate(client.created_at) },
    {
      header: 'Ações',
      accessor: (client: any) => (
        <div className="flex space-x-2">
          <Link href={`/clients/${client.id}`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Eye className="h-4 w-4" />
            </a>
          </Link>
          <Link href={`/clients/${client.id}/edit`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Edit className="h-4 w-4" />
            </a>
          </Link>
          <button
            onClick={() => {
              setSelectedClientId(client.id);
              setIsDeleteModalOpen(true);
            }}
            className="text-red-600 hover:text-red-800"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <Head>
        <title>Clientes | Renum Admin</title>
      </Head>

      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-600">Gerencie os clientes da plataforma</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link href="/clients/new">
            <a>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Novo Cliente
              </Button>
            </a>
          </Link>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <form onSubmit={handleSearch} className="flex w-full sm:w-auto">
              <div className="relative flex-grow">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Buscar clientes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button type="submit" className="ml-2">
                Buscar
              </Button>
            </form>
            <div className="mt-2 sm:mt-0 flex items-center">
              <Button variant="outline" className="flex items-center">
                <Filter className="h-4 w-4 mr-2" />
                Filtros
              </Button>
            </div>
          </div>
        </div>

        <Table
          columns={columns}
          data={clients}
          isLoading={isLoading}
          emptyMessage="Nenhum cliente encontrado"
        />

        {totalPages > 1 && (
          <div className="px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <Button
                variant="outline"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                Próximo
              </Button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando <span className="font-medium">{(page - 1) * pageSize + 1}</span> a{' '}
                  <span className="font-medium">
                    {Math.min(page * pageSize, total)}
                  </span>{' '}
                  de <span className="font-medium">{total}</span> resultados
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Anterior</span>
                    &larr;
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        pageNum === page
                          ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                          : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  ))}
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Próximo</span>
                    &rarr;
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Desativar Cliente"
      >
        <div className="p-6">
          <p className="mb-4">
            Tem certeza que deseja desativar este cliente? Esta ação irá impedir o acesso do cliente à plataforma.
          </p>
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => setIsDeleteModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              isLoading={deactivateClient.isPending}
            >
              Desativar
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}