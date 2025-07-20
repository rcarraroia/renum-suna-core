import { rest } from 'msw';

// Define API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Define handlers for API mocking
export const handlers = [
  // Auth endpoints
  rest.post(`${API_BASE_URL}/api/auth/login`, (req, res, ctx) => {
    const { email, password } = req.body as { email: string; password: string };
    
    // Mock successful login for demo user
    if (email === 'demo@renum.com' && password === 'password') {
      return res(
        ctx.status(200),
        ctx.json({
          user: {
            id: '1',
            name: 'Usuário Demo',
            email: 'demo@renum.com',
            role: 'user'
          },
          token: 'mock-jwt-token'
        })
      );
    }
    
    // Mock failed login
    return res(
      ctx.status(401),
      ctx.json({
        detail: 'Email ou senha incorretos'
      })
    );
  }),
  
  rest.post(`${API_BASE_URL}/api/auth/register`, (req, res, ctx) => {
    const { name, email, password } = req.body as { name: string; email: string; password: string };
    
    // Mock successful registration
    return res(
      ctx.status(201),
      ctx.json({
        user: {
          id: '2',
          name,
          email,
          role: 'user'
        }
      })
    );
  }),
  
  // Agents endpoints
  rest.get(`${API_BASE_URL}/api/agents`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        agents: [
          {
            id: '1',
            name: 'Agente de Suporte',
            description: 'Agente para suporte ao cliente',
            status: 'active',
            created_at: '2025-07-10T14:30:00Z',
            updated_at: '2025-07-15T09:45:00Z',
            configuration: {
              model: 'gpt-4',
              system_prompt: 'Você é um agente de suporte ao cliente',
              tools: []
            },
            knowledge_base_ids: ['1', '2']
          },
          {
            id: '2',
            name: 'Assistente de Pesquisa',
            description: 'Agente para auxiliar em pesquisas',
            status: 'draft',
            created_at: '2025-07-12T10:15:00Z',
            updated_at: '2025-07-12T10:15:00Z',
            configuration: {
              model: 'claude-3-opus',
              system_prompt: 'Você é um assistente de pesquisa',
              tools: []
            },
            knowledge_base_ids: ['3']
          }
        ]
      })
    );
  }),
  
  rest.post(`${API_BASE_URL}/api/agents`, (req, res, ctx) => {
    const agentData = req.body as any;
    
    return res(
      ctx.status(201),
      ctx.json({
        agent: {
          id: '3',
          ...agentData,
          status: agentData.status || 'draft',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      })
    );
  }),
  
  rest.get(`${API_BASE_URL}/api/agents/:id`, (req, res, ctx) => {
    const { id } = req.params;
    
    return res(
      ctx.status(200),
      ctx.json({
        agent: {
          id,
          name: 'Agente de Teste',
          description: 'Descrição do agente de teste',
          status: 'active',
          created_at: '2025-07-10T14:30:00Z',
          updated_at: '2025-07-15T09:45:00Z',
          configuration: {
            model: 'gpt-4',
            system_prompt: 'Você é um agente de teste',
            tools: []
          },
          knowledge_base_ids: ['1', '2']
        }
      })
    );
  }),
  
  // Knowledge base endpoints
  rest.get(`${API_BASE_URL}/api/knowledge-bases`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        knowledge_bases: [
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
          }
        ]
      })
    );
  }),
  
  // Tools endpoints
  rest.get(`${API_BASE_URL}/api/tools`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        tools: [
          {
            id: 'tavily_search',
            name: 'Tavily Search',
            description: 'Pesquisa na web usando a API Tavily',
            category: 'search',
            icon: 'search'
          },
          {
            id: 'web_browser',
            name: 'Navegador Web',
            description: 'Acessa páginas web e extrai conteúdo',
            category: 'web',
            icon: 'chrome'
          },
          {
            id: 'code_interpreter',
            name: 'Interpretador de Código',
            description: 'Executa código Python para análise de dados',
            category: 'code',
            icon: 'code'
          }
        ]
      })
    );
  }),
  
  // Chat endpoints
  rest.post(`${API_BASE_URL}/api/agents/:id/chat`, (req, res, ctx) => {
    const { message } = req.body as { message: string };
    
    return res(
      ctx.status(200),
      ctx.json({
        response: {
          id: Math.random().toString(36).substring(2, 15),
          role: 'assistant',
          content: `Esta é uma resposta simulada para: "${message}"`,
          created_at: new Date().toISOString()
        }
      })
    );
  }),
  
  rest.get(`${API_BASE_URL}/api/agents/:id/conversations`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        messages: [
          {
            id: '1',
            role: 'user',
            content: 'Olá, como posso te ajudar?',
            created_at: '2025-07-18T10:30:00Z'
          },
          {
            id: '2',
            role: 'assistant',
            content: 'Olá! Estou aqui para ajudar com suas perguntas.',
            created_at: '2025-07-18T10:30:05Z'
          }
        ]
      })
    );
  })
];