import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { Client } from '../types/client';

interface UseClientsOptions {
  initialPageSize?: number;
}

export const useClients = (options: UseClientsOptions = {}) => {
  const { initialPageSize = 10 } = options;
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [filter, setFilter] = useState<Record<string, any>>({});
  
  const queryClient = useQueryClient();

  // Função para buscar clientes
  const fetchClients = async () => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: pageSize.toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(search ? { search } : {}),
      ...filter,
    });

    // Simulação de API - remover quando integrar com API real
    // Retorna dados mockados para desenvolvimento
    // Na implementação real, usar:
    // const { data } = await apiClient.get(`/api/v2/admin/clients?${params}`);
    // return data;
    
    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay
    
    const mockClients: Client[] = [
      {
        id: '1',
        name: 'Empresa ABC',
        email: 'contato@empresaabc.com',
        phone: '(11) 1234-5678',
        plan: 'enterprise',
        status: 'active',
        usage_limit: 10000,
        current_usage: 7500,
        created_at: new Date('2023-01-15'),
        updated_at: new Date('2023-06-20'),
      },
      {
        id: '2',
        name: 'Corporação XYZ',
        email: 'admin@corpxyz.com',
        phone: '(21) 9876-5432',
        plan: 'premium',
        status: 'active',
        usage_limit: 5000,
        current_usage: 4200,
        created_at: new Date('2023-02-10'),
        updated_at: new Date('2023-07-05'),
      },
      {
        id: '3',
        name: 'Tech Solutions',
        email: 'contato@techsolutions.com',
        phone: '(31) 3333-4444',
        plan: 'standard',
        status: 'inactive',
        usage_limit: 2000,
        current_usage: 1800,
        created_at: new Date('2023-03-22'),
        updated_at: new Date('2023-05-18'),
      },
      {
        id: '4',
        name: 'Inovação Digital',
        email: 'suporte@inovacaodigital.com',
        phone: '(41) 5555-6666',
        plan: 'basic',
        status: 'pending',
        usage_limit: 1000,
        current_usage: 200,
        created_at: new Date('2023-04-05'),
        updated_at: new Date('2023-04-05'),
      },
      {
        id: '5',
        name: 'Global Services',
        email: 'info@globalservices.com',
        phone: '(51) 7777-8888',
        plan: 'enterprise',
        status: 'active',
        usage_limit: 15000,
        current_usage: 9800,
        created_at: new Date('2023-01-30'),
        updated_at: new Date('2023-08-12'),
      },
    ];
    
    // Filtrar por busca
    let filteredClients = mockClients;
    if (search) {
      const searchLower = search.toLowerCase();
      filteredClients = mockClients.filter(
        client => 
          client.name.toLowerCase().includes(searchLower) || 
          client.email.toLowerCase().includes(searchLower)
      );
    }
    
    // Filtrar por status
    if (filter.status) {
      filteredClients = filteredClients.filter(client => client.status === filter.status);
    }
    
    // Filtrar por plano
    if (filter.plan) {
      filteredClients = filteredClients.filter(client => client.plan === filter.plan);
    }
    
    // Ordenar
    filteredClients.sort((a, b) => {
      const aValue = a[sortBy as keyof Client];
      const bValue = b[sortBy as keyof Client];
      
      if (!aValue || !bValue) return 0;
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    
    // Paginação
    const startIndex = (page - 1) * pageSize;
    const paginatedClients = filteredClients.slice(startIndex, startIndex + pageSize);
    
    return {
      clients: paginatedClients,
      total: filteredClients.length,
      page,
      pageSize,
      totalPages: Math.ceil(filteredClients.length / pageSize),
    };
  };

  // Query para buscar clientes
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['clients', page, pageSize, search, sortBy, sortOrder, filter],
    queryFn: fetchClients,
  });

  // Mutation para criar cliente
  const createClient = useMutation({
    mutationFn: async (clientData: Omit<Client, 'id' | 'created_at' | 'updated_at'>) => {
      // Na implementação real:
      // const { data } = await apiClient.post('/api/v2/admin/clients', clientData);
      // return data;
      
      await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay
      
      return {
        id: Math.random().toString(36).substring(2, 11),
        ...clientData,
        created_at: new Date(),
        updated_at: new Date(),
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  // Mutation para atualizar cliente
  const updateClient = useMutation({
    mutationFn: async ({ id, ...clientData }: Partial<Client> & { id: string }) => {
      // Na implementação real:
      // const { data } = await apiClient.put(`/api/v2/admin/clients/${id}`, clientData);
      // return data;
      
      await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay
      
      return {
        id,
        ...clientData,
        updated_at: new Date(),
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  // Mutation para desativar cliente
  const deactivateClient = useMutation({
    mutationFn: async (id: string) => {
      // Na implementação real:
      // await apiClient.put(`/api/v2/admin/clients/${id}/deactivate`);
      
      await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay
      
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  return {
    clients: data?.clients || [],
    total: data?.total || 0,
    page,
    pageSize,
    totalPages: data?.totalPages || 0,
    isLoading,
    error,
    setPage,
    setPageSize,
    setSearch,
    setSortBy,
    setSortOrder,
    setFilter,
    refetch,
    createClient,
    updateClient,
    deactivateClient,
  };
};