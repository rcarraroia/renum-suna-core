import React, { useState, useEffect } from 'react';
import { Tool, Search, Loader2, AlertCircle } from 'lucide-react';
import { agentApi } from '../lib/api-client';
import Checkbox from './ui/Checkbox';

interface ToolItem {
  id: string;
  name: string;
  description: string;
  category?: string;
  icon?: string;
  requires_configuration?: boolean;
}

interface ToolSelectorProps {
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
}

const ToolSelector: React.FC<ToolSelectorProps> = ({ selectedIds, onChange }) => {
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Tentar buscar ferramentas da API real
      try {
        const response = await agentApi.listTools();
        if (response && response.tools && response.tools.length > 0) {
          setTools(response.tools);
          setIsLoading(false);
          return;
        }
      } catch (apiError) {
        console.warn('Falha ao buscar ferramentas da API, usando dados mockados:', apiError);
      }
      
      // Fallback para dados mockados se a API falhar
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const mockTools: ToolItem[] = [
        {
          id: 'tavily_search',
          name: 'Tavily Search',
          description: 'Pesquisa na web usando a API Tavily para obter informações atualizadas',
          category: 'search',
          icon: 'search'
        },
        {
          id: 'firecrawl',
          name: 'Firecrawl',
          description: 'Web scraping usando a API Firecrawl para extrair dados de sites',
          category: 'web',
          icon: 'globe'
        },
        {
          id: 'web_browser',
          name: 'Navegador Web',
          description: 'Acessa páginas web e extrai conteúdo de forma automatizada',
          category: 'web',
          icon: 'chrome'
        },
        {
          id: 'file_manager',
          name: 'Gerenciador de Arquivos',
          description: 'Cria, lê e modifica arquivos no sistema',
          category: 'files',
          icon: 'file'
        },
        {
          id: 'code_interpreter',
          name: 'Interpretador de Código',
          description: 'Executa código Python para análise de dados e visualizações',
          category: 'code',
          icon: 'code'
        },
        {
          id: 'google_sheets',
          name: 'Google Sheets',
          description: 'Integração com planilhas do Google para análise e manipulação de dados',
          category: 'data',
          icon: 'table',
          requires_configuration: true
        },
        {
          id: 'google_drive',
          name: 'Google Drive',
          description: 'Acesso a arquivos armazenados no Google Drive',
          category: 'files',
          icon: 'cloud',
          requires_configuration: true
        },
        {
          id: 'email_sender',
          name: 'Envio de Email',
          description: 'Envia emails através de serviços SMTP configurados',
          category: 'communication',
          icon: 'mail',
          requires_configuration: true
        },
        {
          id: 'weather_api',
          name: 'API de Clima',
          description: 'Obtém informações meteorológicas atualizadas',
          category: 'api',
          icon: 'cloud-sun'
        },
        {
          id: 'image_generator',
          name: 'Gerador de Imagens',
          description: 'Gera imagens usando modelos de IA como DALL-E ou Stable Diffusion',
          category: 'ai',
          icon: 'image'
        },
        {
          id: 'text_to_speech',
          name: 'Texto para Fala',
          description: 'Converte texto em áudio usando serviços de síntese de voz',
          category: 'ai',
          icon: 'mic'
        }
      ];
      
      setTools(mockTools);
    } catch (err: any) {
      console.error('Erro ao carregar ferramentas:', err);
      setError(err.message || 'Erro ao carregar ferramentas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleTool = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(selectedId => selectedId !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  // Filtrar ferramentas pelo termo de busca
  const filteredTools = tools.filter(tool => 
    tool.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    tool.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Agrupar ferramentas por categoria
  const groupedTools: Record<string, ToolItem[]> = {};
  filteredTools.forEach(tool => {
    const category = tool.category || 'other';
    if (!groupedTools[category]) {
      groupedTools[category] = [];
    }
    groupedTools[category].push(tool);
  });

  // Traduzir categorias
  const categoryNames: Record<string, string> = {
    search: 'Pesquisa',
    web: 'Web',
    files: 'Arquivos',
    code: 'Código',
    data: 'Dados',
    communication: 'Comunicação',
    api: 'APIs',
    ai: 'Inteligência Artificial',
    other: 'Outras'
  };

  // Ordenar categorias para exibição
  const orderedCategories = Object.keys(groupedTools).sort((a, b) => {
    // Colocar categorias específicas primeiro
    const order = ['search', 'web', 'files', 'code', 'data', 'ai', 'api', 'communication', 'other'];
    return order.indexOf(a) - order.indexOf(b);
  });

  return (
    <div className="space-y-4">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Buscar ferramentas..."
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
            onClick={fetchTools}
            className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
          >
            Tentar novamente
          </button>
        </div>
      ) : filteredTools.length > 0 ? (
        <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
          {orderedCategories.map((category) => (
            <div key={category} className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">
                {categoryNames[category] || category}
              </h4>
              {groupedTools[category].map((tool) => (
                <div
                  key={tool.id}
                  className={`border rounded-md p-3 ${
                    selectedIds.includes(tool.id)
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Checkbox
                    id={`tool-${tool.id}`}
                    label={tool.name}
                    description={`${tool.description}${tool.requires_configuration ? ' (Requer configuração adicional)' : ''}`}
                    checked={selectedIds.includes(tool.id)}
                    onChange={() => handleToggleTool(tool.id)}
                  />
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 border border-dashed border-gray-300 rounded-md">
          <Tool className="h-12 w-12 text-gray-400 mx-auto" />
          <p className="mt-2 text-gray-500">
            {searchTerm
              ? 'Nenhuma ferramenta encontrada com esse termo'
              : 'Nenhuma ferramenta disponível'}
          </p>
        </div>
      )}

      <div className="flex justify-between text-sm text-gray-500">
        <span>{selectedIds.length} selecionadas</span>
        <button
          type="button"
          onClick={() => onChange([])}
          className="text-indigo-600 hover:text-indigo-500"
          disabled={selectedIds.length === 0}
        >
          Limpar seleção
        </button>
      </div>
    </div>
  );
};

export default ToolSelector;