import React, { useState } from 'react';
import Head from 'next/head';
import { Plus, Edit, Trash2, Power, PowerOff, MoveUp, MoveDown } from 'lucide-react';
import { useHomepage } from '../../../hooks/useHomepage';
import { TypewriterPhrase } from '../../../types/homepage';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import Table from '../../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import PhraseForm from '../../../components/homepage/PhraseForm';
import TypewriterPreview from '../../../components/homepage/TypewriterPreview';
import { formatDate } from '../../../lib/utils';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function HomepagePhrases() {
  const {
    phrases,
    isLoadingPhrases,
    createPhrase,
    isCreatingPhrase,
    updatePhrase,
    isUpdatingPhrase,
    deletePhrase,
    isDeletingPhrase,
    togglePhraseStatus,
    isTogglingPhraseStatus,
    reorderPhrases,
    isReorderingPhrases,
    error,
    setError,
  } = useHomepage();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [selectedPhrase, setSelectedPhrase] = useState<TypewriterPhrase | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleOpenCreateModal = () => {
    setSelectedPhrase(null);
    setIsEditing(false);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (phrase: TypewriterPhrase) => {
    setSelectedPhrase(phrase);
    setIsEditing(true);
    setIsFormModalOpen(true);
  };

  const handleOpenDeleteModal = (phrase: TypewriterPhrase) => {
    setSelectedPhrase(phrase);
    setIsDeleteModalOpen(true);
  };

  const handleSubmitPhrase = async (data: any) => {
    try {
      const formattedData = {
        ...data,
        is_active: data.is_active === 'true' || data.is_active === true,
      };

      if (isEditing && selectedPhrase) {
        await updatePhrase({
          id: selectedPhrase.id,
          data: formattedData,
        });
      } else {
        await createPhrase(formattedData);
      }
      setIsFormModalOpen(false);
    } catch (error) {
      // Error already handled in the hook
    }
  };

  const handleDeletePhrase = async () => {
    if (!selectedPhrase) return;

    try {
      await deletePhrase(selectedPhrase.id);
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Error already handled in the hook
    }
  };

  const handleToggleStatus = async (id: string, isActive: boolean) => {
    try {
      await togglePhraseStatus({ id, isActive });
    } catch (error) {
      // Error already handled in the hook
    }
  };

  const handleMovePhrase = async (index: number, direction: 'up' | 'down') => {
    if (!phrases) return;
    
    // Create a copy of the phrases array sorted by display_order
    const sortedPhrases = [...phrases].sort((a, b) => a.display_order - b.display_order);
    
    // Can't move the first item up or the last item down
    if ((direction === 'up' && index === 0) || 
        (direction === 'down' && index === sortedPhrases.length - 1)) {
      return;
    }
    
    // Swap the display_order values
    const newPhrases = [...sortedPhrases];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    // Create a new array with the updated order
    const reorderedIds = newPhrases.map(phrase => phrase.id);
    // Swap the positions in the array
    [reorderedIds[index], reorderedIds[targetIndex]] = [reorderedIds[targetIndex], reorderedIds[index]];
    
    try {
      await reorderPhrases(reorderedIds);
    } catch (error) {
      // Error already handled in the hook
    }
  };

  const columns = [
    { header: 'Texto', accessor: 'text' },
    { header: 'Ordem', accessor: 'display_order' },
    { 
      header: 'Status', 
      accessor: (row: TypewriterPhrase) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
        >
          {row.is_active ? 'Ativo' : 'Inativo'}
        </span>
      )
    },
    { header: 'Criado em', accessor: (row: TypewriterPhrase) => formatDate(row.created_at) },
    { header: 'Atualizado em', accessor: (row: TypewriterPhrase) => formatDate(row.updated_at) },
    {
      header: 'Ações',
      accessor: (row: TypewriterPhrase, index: number) => {
        const sortedPhrases = phrases ? [...phrases].sort((a, b) => a.display_order - b.display_order) : [];
        const sortedIndex = sortedPhrases.findIndex(p => p.id === row.id);
        
        return (
          <div className="flex space-x-2">
            <button
              onClick={() => handleMovePhrase(sortedIndex, 'up')}
              className="text-gray-600 hover:text-gray-800"
              disabled={sortedIndex === 0 || isReorderingPhrases}
              title="Mover para cima"
            >
              <MoveUp className="h-5 w-5" />
            </button>
            <button
              onClick={() => handleMovePhrase(sortedIndex, 'down')}
              className="text-gray-600 hover:text-gray-800"
              disabled={sortedIndex === sortedPhrases.length - 1 || isReorderingPhrases}
              title="Mover para baixo"
            >
              <MoveDown className="h-5 w-5" />
            </button>
            <button
              onClick={() => handleToggleStatus(row.id, !row.is_active)}
              className={`${row.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`}
              disabled={isTogglingPhraseStatus}
              title={row.is_active ? 'Desativar' : 'Ativar'}
            >
              {row.is_active ? (
                <PowerOff className="h-5 w-5" />
              ) : (
                <Power className="h-5 w-5" />
              )}
            </button>
            <button
              onClick={() => handleOpenEditModal(row)}
              className="text-blue-600 hover:text-blue-800"
              title="Editar"
            >
              <Edit className="h-5 w-5" />
            </button>
            <button
              onClick={() => handleOpenDeleteModal(row)}
              className="text-red-600 hover:text-red-800"
              title="Excluir"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Frases da Página Inicial</title>
        <meta name="description" content="Gerenciar frases da página inicial" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Frases da Página Inicial</h1>
            <p className="text-gray-600">Gerencie as frases com efeito de máquina de escrever na página inicial</p>
          </div>
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setIsPreviewModalOpen(true)}
            >
              Visualizar Efeito
            </Button>
            <Button onClick={handleOpenCreateModal}>
              <Plus className="h-4 w-4 mr-2" /> Nova Frase
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

        <Card>
          <CardHeader>
            <CardTitle>Frases da Página Inicial</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              columns={columns}
              data={phrases ? [...phrases].sort((a, b) => a.display_order - b.display_order) : []}
              isLoading={isLoadingPhrases}
              emptyMessage="Nenhuma frase encontrada"
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          title={isEditing ? 'Editar Frase' : 'Nova Frase'}
        >
          <PhraseForm
            defaultValues={
              selectedPhrase
                ? {
                    text: selectedPhrase.text,
                    display_order: selectedPhrase.display_order,
                    is_active: selectedPhrase.is_active,
                  }
                : undefined
            }
            onSubmit={handleSubmitPhrase}
            isSubmitting={isCreatingPhrase || isUpdatingPhrase}
            isEditMode={isEditing}
          />
        </Modal>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Frase"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir esta frase?
            </p>
            <p className="mb-2 font-medium">"{selectedPhrase?.text}"</p>
            <p className="mb-4 text-red-600">
              Esta ação não pode ser desfeita.
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
                onClick={handleDeletePhrase}
                isLoading={isDeletingPhrase}
              >
                Excluir
              </Button>
            </div>
          </div>
        </Modal>

        <Modal
          isOpen={isPreviewModalOpen}
          onClose={() => setIsPreviewModalOpen(false)}
          title="Visualização do Efeito de Máquina de Escrever"
          size="lg"
        >
          <div className="p-4">
            <TypewriterPreview phrases={phrases || []} />
            <p className="mt-6 text-sm text-gray-500 text-center">
              Esta é uma visualização de como o efeito de máquina de escrever aparecerá na página inicial.
              Apenas frases ativas serão exibidas na ordem especificada.
            </p>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}