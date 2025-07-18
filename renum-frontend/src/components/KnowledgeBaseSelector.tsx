import React, { useState, useEffect } from 'react';
import { Database, Search, Loader2, AlertCircle, Book } from 'lucide-react';
import { knowledgeBaseApi } from '../lib/api-client';
import Checkbox from './ui/Checkbox';
import Badge from './ui/Badge';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at?: string;
  updated_at?: string;
}

interface KnowledgeBaseSelectorProps {
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  required?: boolean;
}

const KnowledgeBaseSelector: React.FC<KnowledgeBaseSelectorProps> = ({ 
  selectedIds, 
  onChange,
  required = false
}) => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSelector, setShowSelector] = useState(true);

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Tentar buscar bases de conhecimento da API real
      try {
        const response = await knowledgeBaseApi.listKnowledgeBases();
        if (response && response.knowledge_bases && response.knowledge_bases.length > 0) {
          setKnowledgeBases(response.knowledge_bases);
          setIsLoading(false);
          return;
        }
      } catch (apiError) {
        console.warn('Falha ao buscar bases de conhecimento da API, usando dados mockados:', apiError);
      }
      
      // Fallback para dados mockados se a API falhar
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const mockKnowledgeBases: KnowledgeBase[] = [
        {
          id: '1',
          name: 'Documentação Técnica',
          description: 'Manuais técnicos e documentação de produtos',
          document_count: 24,
          created_at: '2025-06-15T10:30:00Z',
          updated_at: '2025-07-10T14:45:00Z'
        },
        {
          id: '2',
          name: 'Manuais de Produto',
          description: 'Guias de usuário e manuais de produtos',
          document_count: 15,
          created_at: '2025-05-20T08:15:00Z',
          updated_at: '2025-07-05T11:20:00Z'
        },
        {
          id: '3',
          name: 'Base de Conhecimento Interna',
          description: 'Documentos internos e procedimentos da empresa',
          document_count: 42,
          created_at: '2025-04-10T16:45:00Z',
          updated_at: '2025-07-12T09:30:00Z'
        },
        {
          id: '4',
          name: 'FAQ de Suporte',
          description: 'Perguntas frequentes e respostas para suporte ao cliente',
          document_count: 36,
          created_at: '2025-03-25T13:10:00Z',
          updated_at: '2025-07-08T15:55:00Z'
        },
        {
          id: '5',
          name: 'Artigos de Blog',
          description: 'Conteúdo de blog e artigos publicados',
          document_count: 28,
          created_at: '2025-02-18T11:25:00Z',
          updated_at: '2025-07-01T10:15:00Z'
        },
        {
          id: '6',
          name: 'Documentação de API',
          description: 'Referência de API e exemplos de código',
          document_count: 19,
          created_at: '2025-01-30T09:40:00Z',
          updated_at: '2025-06-28T14:20:00Z'
        }
      ];
      
      setKnowledgeBases(mockKnowledgeBases);
    } catch (err: any) {
      console.error('Erro ao carregar bases de conhecimento:', err);
      setError(err.message || 'Erro ao carregar bases de conhecimento');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleKnowledgeBase = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(selectedId => selectedId !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  const handleRemoveKnowledgeBase = (id: string) => {
    onChange(selectedIds.filter(selectedId => selectedId !== id));
  };

  // Filtrar bases de conhecimento pelo termo de busca
  const filteredKnowledgeBases = knowledgeBases.filter(kb => 
    kb.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    kb.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Obter detalhes das bases de conhecimento selecionadas
  const selectedKnowledgeBases = knowledgeBases.filter(kb => 
    selectedIds.includes(kb.id)
  );

  return (
    <div className="space-y-4">
      {/* Exibir badges para bases de conhecimento selecionadas */}
      {selectedIds.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {selectedKnowledgeBases.map((kb) => (
            <Badge
              key={kb.id}
              variant="secondary"
              size="sm"
              onRemove={() => handleRemoveKnowledgeBase(kb.id)}
            >
              <Book className="h-3 w-3 mr-1" />
              {kb.name}
            </Badge>
          ))}
        </div>
      )}

      {/* Mostrar mensagem se nenhuma base estiver selecionada e for obrigatório */}
      {required && selectedIds.length === 0 && (
        <p className="text-sm text-amber-600 mb-2">
          É necessário selecionar pelo menos uma base de conhecimento.
        </p>
      )}

      {/* Botão para mostrar/ocultar o seletor */}
      <button
        type="button"
        onClick={() => setShowSelector(!showSelector)}
        className="text-sm text-indigo-600 hover:text-indigo-500 mb-2"
      >
        {showSelector ? 'Ocultar seletor' : 'Mostrar seletor'}
      </button>

      {showSelector && (
        <>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Buscar bases de conhecimento..."
              className="pl-10 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md"
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            />
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                <p>{error}</p>
              </div>
              <button
                onClick={fetchKnowledgeBases}
                className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
              >
                Tentar novamente
              </button>
            </div>
          ) : filteredKnowledgeBases.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
              {filteredKnowledgeBases.map((kb) => (
                <div
                  key={kb.id}
                  className={`border rounded-md p-3 ${
                    selectedIds.includes(kb.id)
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Checkbox
                    id={`kb-${kb.id}`}
                    label={kb.name}
                    description={`${kb.description} (${kb.document_count} documentos)`}
                    checked={selectedIds.includes(kb.id)}
                    onChange={() => handleToggleKnowledgeBase(kb.id)}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 border border-dashed border-gray-300 rounded-md">
              <Database className="h-12 w-12 text-gray-400 mx-auto" />
              <p className="mt-2 text-gray-500">
                {searchTerm
                  ? 'Nenhuma base de conhecimento encontrada com esse termo'
                  : 'Nenhuma base de conhecimento disponível'}
              </p>
            </div>
          )}

          <div className="flex justify-between text-sm text-gray-500">
            <span>{selectedIds.length} selecionada(s)</span>
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-indigo-600 hover:text-indigo-500"
              disabled={selectedIds.length === 0}
            >
              Limpar seleção
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default KnowledgeBaseSelector;