import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import { Team } from '../../services/api-types';
import { useTeams } from '../../services/react-query-hooks';
import PageHeader from '../../components/common/PageHeader';
import SearchFilter from '../../components/common/SearchFilter';
import EmptyState from '../../components/common/EmptyState';
import TeamCard from '../../components/teams/TeamCard';
import Link from 'next/link';

/**
 * Página de listagem de equipes
 */
const TeamsPage: React.FC = () => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;
  
  // Busca as equipes usando React Query
  const { data, isLoading, error, refetch } = useTeams(
    { page: currentPage, limit: pageSize, search: searchTerm },
    { placeholderData: (previousData) => previousData }
  );
  
  // Manipuladores de eventos
  const handleSearch = useCallback((value: string) => {
    setSearchTerm(value);
    setCurrentPage(1); // Volta para a primeira página ao buscar
  }, []);
  
  const handleExecute = useCallback((team: Team) => {
    router.push(`/teams/${team.team_id}/execute`);
  }, [router]);
  
  const handleEdit = useCallback((team: Team) => {
    router.push(`/teams/${team.team_id}/edit`);
  }, [router]);
  
  const handleDelete = useCallback((team: Team) => {
    // Aqui seria implementada a lógica de confirmação e exclusão
    if (confirm(`Tem certeza que deseja excluir a equipe "${team.name}"?`)) {
      // Chamar API para excluir
      console.log('Excluir equipe:', team.team_id);
    }
  }, []);
  
  // Renderiza as ações do cabeçalho
  const renderHeaderActions = () => (
    <Link
      href="/teams/new"
      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      <svg
        className="-ml-1 mr-2 h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
          clipRule="evenodd"
        />
      </svg>
      Nova Equipe
    </Link>
  );
  
  // Renderiza o estado vazio
  const renderEmptyState = () => (
    <EmptyState
      title="Nenhuma equipe encontrada"
      description={
        searchTerm
          ? "Não encontramos nenhuma equipe com os critérios de busca informados. Tente ajustar sua busca."
          : "Você ainda não criou nenhuma equipe. Crie sua primeira equipe para começar."
      }
      icon={
        <svg
          className="h-6 w-6 text-gray-400"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
      }
      action={
        <Link
          href="/teams/new"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Criar Equipe
        </Link>
      }
    />
  );
  
  // Renderiza a paginação
  const renderPagination = () => {
    if (!data || data.total <= pageSize) return null;
    
    const totalPages = data.pages;
    
    return (
      <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 mt-4">
        <div className="flex flex-1 justify-between sm:hidden">
          <button
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className={`relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 ${
              currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'
            }`}
          >
            Anterior
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className={`relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 ${
              currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'
            }`}
          >
            Próxima
          </button>
        </div>
        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Mostrando <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> a{' '}
              <span className="font-medium">
                {Math.min(currentPage * pageSize, data.total)}
              </span>{' '}
              de <span className="font-medium">{data.total}</span> resultados
            </p>
          </div>
          <div>
            <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className={`relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 ${
                  currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'
                }`}
              >
                <span className="sr-only">Anterior</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                </svg>
              </button>
              
              {/* Renderiza os números de página */}
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                    page === currentPage
                      ? 'z-10 bg-blue-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                      : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-offset-0'
                  }`}
                >
                  {page}
                </button>
              ))}
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className={`relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 ${
                  currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'
                }`}
              >
                <span className="sr-only">Próxima</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    );
  };
  
  // Renderiza o conteúdo principal
  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-4">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium">Erro ao carregar equipes</p>
              <p className="text-sm">{error instanceof Error ? error.message : 'Ocorreu um erro desconhecido'}</p>
              <button
                onClick={() => refetch()}
                className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    if (!data || data.items.length === 0) {
      return renderEmptyState();
    }
    
    return (
      <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map(team => (
            <TeamCard
              key={team.team_id}
              team={team}
              onExecute={handleExecute}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
        {renderPagination()}
      </>
    );
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title="Equipes de Agentes"
        description="Gerencie suas equipes de agentes para execução de tarefas complexas"
        actions={renderHeaderActions()}
      />
      
      <div className="mb-6">
        <SearchFilter
          placeholder="Buscar equipes..."
          value={searchTerm}
          onChange={handleSearch}
          className="max-w-md"
        />
      </div>
      
      {renderContent()}
    </div>
  );
};

export default TeamsPage;