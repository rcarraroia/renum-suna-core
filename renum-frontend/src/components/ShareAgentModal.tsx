import React, { useState, useEffect } from 'react';
import { Dialog } from '@radix-ui/react-dialog';
import { X, UserPlus, Trash2, Edit2 } from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import Button from './ui/Button';
import Input from './ui/Input';
import Select from './ui/Select';
import Alert from './ui/Alert';
import { apiClient } from '../lib/api-client';
import { useToast } from '../hooks/useToast';

// Tipos
type PermissionLevel = 'view' | 'use' | 'edit' | 'admin';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AgentShare {
  id: string;
  agent_id: string;
  user_id: string;
  permission_level: PermissionLevel;
  created_at: string;
  created_by: string;
  expires_at: string | null;
  user?: {
    name: string;
    email: string;
  };
}

interface ShareAgentModalProps {
  agentId: string;
  isOpen: boolean;
  onClose: () => void;
}

interface ShareFormData {
  userId: string;
  permissionLevel: PermissionLevel;
  daysValid: number | null;
}

const permissionOptions = [
  { value: 'view', label: 'Visualizar' },
  { value: 'use', label: 'Utilizar' },
  { value: 'edit', label: 'Editar' },
  { value: 'admin', label: 'Administrar' },
];

const expirationOptions = [
  { value: null, label: 'Sem expiração' },
  { value: 7, label: '7 dias' },
  { value: 30, label: '30 dias' },
  { value: 90, label: '90 dias' },
  { value: 365, label: '1 ano' },
];

const ShareAgentModal: React.FC<ShareAgentModalProps> = ({ agentId, isOpen, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editingShare, setEditingShare] = useState<AgentShare | null>(null);
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  
  const { register, handleSubmit, control, reset, setValue, formState: { errors } } = useForm<ShareFormData>({
    defaultValues: {
      userId: '',
      permissionLevel: 'view',
      daysValid: null,
    }
  });

  // Buscar usuários
  const { data: users, isLoading: isLoadingUsers } = useQuery({
    queryKey: ['users', searchTerm],
    queryFn: async () => {
      if (!searchTerm || searchTerm.length < 3) return [];
      const response = await apiClient.get(`/api/v2/users/search?q=${encodeURIComponent(searchTerm)}`);
      return response.data.users;
    },
    enabled: searchTerm.length >= 3,
  });

  // Buscar compartilhamentos existentes
  const { data: shares, isLoading: isLoadingShares } = useQuery({
    queryKey: ['agent-shares', agentId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v2/agents/${agentId}/shares`);
      return response.data.shares;
    },
    enabled: isOpen,
  });

  // Mutação para compartilhar agente
  const shareAgentMutation = useMutation({
    mutationFn: async (data: ShareFormData) => {
      return apiClient.post(`/api/v2/agents/${agentId}/share`, {
        user_id: data.userId,
        permission_level: data.permissionLevel,
        days_valid: data.daysValid,
      });
    },
    onSuccess: () => {
      showToast({
        title: 'Agente compartilhado',
        description: 'O agente foi compartilhado com sucesso.',
        type: 'success',
      });
      reset();
      setSelectedUser(null);
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao compartilhar',
        description: error.response?.data?.detail || 'Ocorreu um erro ao compartilhar o agente.',
        type: 'error',
      });
    },
  });

  // Mutação para atualizar compartilhamento
  const updateShareMutation = useMutation({
    mutationFn: async (data: { shareId: string, updateData: Partial<ShareFormData> }) => {
      return apiClient.put(`/api/v2/agents/${agentId}/shares/${data.shareId}`, {
        permission_level: data.updateData.permissionLevel,
        days_valid: data.updateData.daysValid,
      });
    },
    onSuccess: () => {
      showToast({
        title: 'Compartilhamento atualizado',
        description: 'O compartilhamento foi atualizado com sucesso.',
        type: 'success',
      });
      setEditingShare(null);
      reset();
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao atualizar',
        description: error.response?.data?.detail || 'Ocorreu um erro ao atualizar o compartilhamento.',
        type: 'error',
      });
    },
  });

  // Mutação para remover compartilhamento
  const removeShareMutation = useMutation({
    mutationFn: async (shareId: string) => {
      return apiClient.delete(`/api/v2/agents/${agentId}/shares/${shareId}`);
    },
    onSuccess: () => {
      showToast({
        title: 'Compartilhamento removido',
        description: 'O compartilhamento foi removido com sucesso.',
        type: 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao remover',
        description: error.response?.data?.detail || 'Ocorreu um erro ao remover o compartilhamento.',
        type: 'error',
      });
    },
  });

  // Resetar formulário quando o modal é fechado
  useEffect(() => {
    if (!isOpen) {
      reset();
      setSelectedUser(null);
      setEditingShare(null);
      setSearchTerm('');
    }
  }, [isOpen, reset]);

  // Atualizar formulário quando um compartilhamento é selecionado para edição
  useEffect(() => {
    if (editingShare) {
      setValue('permissionLevel', editingShare.permission_level);
      
      // Calcular dias restantes se houver data de expiração
      if (editingShare.expires_at) {
        const expiresAt = new Date(editingShare.expires_at);
        const now = new Date();
        const daysRemaining = Math.ceil((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        
        // Encontrar a opção mais próxima
        const closestOption = expirationOptions.find(option => option.value && option.value >= daysRemaining);
        setValue('daysValid', closestOption?.value || null);
      } else {
        setValue('daysValid', null);
      }
    }
  }, [editingShare, setValue]);

  // Selecionar usuário da lista de resultados
  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    setValue('userId', user.id);
    setSearchTerm('');
  };

  // Enviar formulário de compartilhamento
  const onSubmit = (data: ShareFormData) => {
    if (editingShare) {
      updateShareMutation.mutate({
        shareId: editingShare.id,
        updateData: {
          permissionLevel: data.permissionLevel,
          daysValid: data.daysValid,
        },
      });
    } else {
      shareAgentMutation.mutate(data);
    }
  };

  // Cancelar edição
  const handleCancelEdit = () => {
    setEditingShare(null);
    reset();
  };

  // Remover compartilhamento
  const handleRemoveShare = (shareId: string) => {
    if (window.confirm('Tem certeza que deseja remover este compartilhamento?')) {
      removeShareMutation.mutate(shareId);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
          <div className="flex justify-between items-center p-4 border-b">
            <h2 className="text-xl font-semibold">Compartilhar Agente</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <X size={20} />
            </button>
          </div>
          
          <div className="p-4 overflow-y-auto max-h-[calc(90vh-130px)]">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {!editingShare ? (
                <>
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">Usuário</label>
                    {selectedUser ? (
                      <div className="flex items-center justify-between p-2 border rounded-md">
                        <div>
                          <p className="font-medium">{selectedUser.name}</p>
                          <p className="text-sm text-gray-500">{selectedUser.email}</p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedUser(null)}
                        >
                          Alterar
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Input
                          placeholder="Buscar usuário por nome ou email"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        
                        {isLoadingUsers && <p className="text-sm text-gray-500">Buscando usuários...</p>}
                        
                        {users && users.length > 0 && (
                          <div className="border rounded-md max-h-40 overflow-y-auto">
                            {users.map((user: User) => (
                              <div
                                key={user.id}
                                className="p-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                                onClick={() => handleSelectUser(user)}
                              >
                                <p className="font-medium">{user.name}</p>
                                <p className="text-sm text-gray-500">{user.email}</p>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {searchTerm.length >= 3 && users && users.length === 0 && (
                          <p className="text-sm text-gray-500">Nenhum usuário encontrado</p>
                        )}
                        
                        <input
                          type="hidden"
                          {...register('userId', { required: 'Selecione um usuário' })}
                        />
                        {errors.userId && (
                          <p className="text-sm text-red-500">{errors.userId.message}</p>
                        )}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="bg-gray-50 p-3 rounded-md mb-4">
                  <p className="font-medium">Editando compartilhamento</p>
                  <p className="text-sm text-gray-500">
                    {editingShare.user?.name} ({editingShare.user?.email})
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nível de Permissão
                  </label>
                  <Controller
                    name="permissionLevel"
                    control={control}
                    rules={{ required: 'Selecione um nível de permissão' }}
                    render={({ field }) => (
                      <Select
                        value={field.value}
                        onChange={field.onChange}
                        options={permissionOptions}
                        placeholder="Selecione o nível de permissão"
                      />
                    )}
                  />
                  {errors.permissionLevel && (
                    <p className="text-sm text-red-500 mt-1">{errors.permissionLevel.message}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expiração
                  </label>
                  <Controller
                    name="daysValid"
                    control={control}
                    render={({ field }) => (
                      <Select
                        value={field.value === null ? null : field.value.toString()}
                        onChange={(value) => field.onChange(value === null ? null : parseInt(value))}
                        options={expirationOptions}
                        placeholder="Selecione o período de expiração"
                      />
                    )}
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 pt-2">
                {editingShare && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancelEdit}
                  >
                    Cancelar
                  </Button>
                )}
                <Button
                  type="submit"
                  disabled={shareAgentMutation.isPending || updateShareMutation.isPending || (!selectedUser && !editingShare)}
                >
                  {editingShare ? 'Atualizar' : 'Compartilhar'}
                </Button>
              </div>
            </form>
            
            <div className="mt-8">
              <h3 className="text-lg font-medium mb-2">Compartilhamentos</h3>
              
              {isLoadingShares ? (
                <p className="text-sm text-gray-500">Carregando compartilhamentos...</p>
              ) : shares && shares.length > 0 ? (
                <div className="border rounded-md overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Usuário
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Permissão
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Expiração
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {shares.map((share: AgentShare) => (
                        <tr key={share.id}>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div>
                              <p className="font-medium">{share.user?.name || 'Usuário'}</p>
                              <p className="text-sm text-gray-500">{share.user?.email || share.user_id}</p>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            {share.permission_level === 'view' && 'Visualizar'}
                            {share.permission_level === 'use' && 'Utilizar'}
                            {share.permission_level === 'edit' && 'Editar'}
                            {share.permission_level === 'admin' && 'Administrar'}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            {share.expires_at ? (
                              <span>
                                {new Date(share.expires_at).toLocaleDateString()}
                              </span>
                            ) : (
                              <span className="text-gray-500">Sem expiração</span>
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right">
                            <div className="flex justify-end space-x-2">
                              <button
                                onClick={() => setEditingShare(share)}
                                className="text-blue-600 hover:text-blue-800"
                                title="Editar"
                              >
                                <Edit2 size={16} />
                              </button>
                              <button
                                onClick={() => handleRemoveShare(share.id)}
                                className="text-red-600 hover:text-red-800"
                                title="Remover"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Alert variant="info">
                  Este agente ainda não foi compartilhado com ninguém.
                </Alert>
              )}
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
};

export default ShareAgentModal;