-- SCRIPT DE MIGRAÇÃO COMPLETA PARA O SISTEMA RENUM (VERSÃO CORRIGIDA)
-- Este script corrige as inconsistências de nomenclatura e cria todas as tabelas necessárias

-- Criar extensão uuid-ossp se ainda não existir
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- PARTE 1: RENOMEAR TABELAS DO MÓDULO RAG PARA USAR PREFIXO RENUM_
-- ========================================

-- Renomear tabelas do módulo RAG para seguir a convenção de nomenclatura
ALTER TABLE IF EXISTS knowledge_bases RENAME TO renum_knowledge_bases;
ALTER TABLE IF EXISTS knowledge_collections RENAME TO renum_knowledge_collections;
ALTER TABLE IF EXISTS documents RENAME TO renum_documents;
ALTER TABLE IF EXISTS document_chunks RENAME TO renum_document_chunks;
ALTER TABLE IF EXISTS document_versions RENAME TO renum_document_versions;
ALTER TABLE IF EXISTS document_usage_stats RENAME TO renum_document_usage_stats;
ALTER TABLE IF EXISTS retrieval_feedback RENAME TO renum_retrieval_feedback;
ALTER TABLE IF EXISTS processing_jobs RENAME TO renum_processing_jobs;
ALTER TABLE IF EXISTS client_plans RENAME TO renum_client_plans;

-- ========================================
-- PARTE 2: CRIAR TABELAS PRINCIPAIS DO SISTEMA RENUM
-- ========================================

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS renum_clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    plan_type TEXT NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabela de usuários (relacionados aos clientes)
CREATE TABLE IF NOT EXISTS renum_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES renum_clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(auth_user_id, client_id)
);

-- Tabela de agentes
CREATE TABLE IF NOT EXISTS renum_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES renum_clients(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    name TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT,
    model TEXT NOT NULL DEFAULT 'gpt-3.5-turbo',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabela de threads (conversas)
CREATE TABLE IF NOT EXISTS renum_threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES renum_clients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES renum_agents(id) ON DELETE SET NULL,
    title TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabela de mensagens
CREATE TABLE IF NOT EXISTS renum_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID NOT NULL REFERENCES renum_threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    model_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ========================================
-- PARTE 3: CRIAR TABELAS DO PAINEL ADMINISTRATIVO
-- ========================================

-- Tabela de administradores
CREATE TABLE IF NOT EXISTS renum_admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin', 'superadmin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Tabela de credenciais administrativas
CREATE TABLE IF NOT EXISTS renum_admin_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES renum_admins(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    credential_type TEXT NOT NULL CHECK (credential_type IN ('api_key', 'oauth_token', 'service_account')),
    encrypted_value TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Tabela de configurações do sistema
CREATE TABLE IF NOT EXISTS renum_system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT NOT NULL,
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by UUID NOT NULL REFERENCES renum_admins(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Tabela de logs de auditoria (renomeada para evitar conflito)
CREATE TABLE IF NOT EXISTS renum_admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    actor_id UUID,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'admin', 'system')),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ========================================
-- PARTE 4: CRIAR TABELA DE COMPARTILHAMENTO DE AGENTES
-- ========================================

-- Tabela de compartilhamento de agentes (corrigida para usar as tabelas corretas)
CREATE TABLE IF NOT EXISTS renum_agent_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES renum_agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES renum_clients(id) ON DELETE CASCADE,
    permission_level TEXT NOT NULL DEFAULT 'view',
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(agent_id, user_id)
);

-- ========================================
-- PARTE 5: CRIAR ÍNDICES
-- ========================================

-- Índices para renum_users
CREATE INDEX IF NOT EXISTS idx_renum_users_auth_user_id ON renum_users(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_renum_users_client_id ON renum_users(client_id);

-- Índices para renum_agents
CREATE INDEX IF NOT EXISTS idx_renum_agents_client_id ON renum_agents(client_id);
CREATE INDEX IF NOT EXISTS idx_renum_agents_created_by ON renum_agents(created_by);

-- Índices para renum_threads
CREATE INDEX IF NOT EXISTS idx_renum_threads_client_id ON renum_threads(client_id);
CREATE INDEX IF NOT EXISTS idx_renum_threads_user_id ON renum_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_threads_agent_id ON renum_threads(agent_id);

-- Índices para renum_messages
CREATE INDEX IF NOT EXISTS idx_renum_messages_thread_id ON renum_messages(thread_id);

-- Índices para renum_agent_shares
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_agent_id ON renum_agent_shares(agent_id);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_user_id ON renum_agent_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_client_id ON renum_agent_shares(client_id);

-- ========================================
-- PARTE 6: CRIAR TRIGGERS PARA UPDATED_AT
-- ========================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para as tabelas principais
DROP TRIGGER IF EXISTS update_renum_clients_updated_at ON renum_clients;
CREATE TRIGGER update_renum_clients_updated_at
BEFORE UPDATE ON renum_clients
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_users_updated_at ON renum_users;
CREATE TRIGGER update_renum_users_updated_at
BEFORE UPDATE ON renum_users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_agents_updated_at ON renum_agents;
CREATE TRIGGER update_renum_agents_updated_at
BEFORE UPDATE ON renum_agents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_threads_updated_at ON renum_threads;
CREATE TRIGGER update_renum_threads_updated_at
BEFORE UPDATE ON renum_threads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Triggers para as tabelas administrativas
DROP TRIGGER IF EXISTS update_renum_admins_updated_at ON renum_admins;
CREATE TRIGGER update_renum_admins_updated_at
BEFORE UPDATE ON renum_admins
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_admin_credentials_updated_at ON renum_admin_credentials;
CREATE TRIGGER update_renum_admin_credentials_updated_at
BEFORE UPDATE ON renum_admin_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_system_settings_updated_at ON renum_system_settings;
CREATE TRIGGER update_renum_system_settings_updated_at
BEFORE UPDATE ON renum_system_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renum_agent_shares_updated_at ON renum_agent_shares;
CREATE TRIGGER update_renum_agent_shares_updated_at
BEFORE UPDATE ON renum_agent_shares
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- PARTE 7: CONFIGURAR RLS (ROW LEVEL SECURITY)
-- ========================================

-- Habilitar RLS nas tabelas
ALTER TABLE renum_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_agent_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_admin_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_admin_audit_logs ENABLE ROW LEVEL SECURITY;

-- Políticas básicas (podem ser refinadas posteriormente)
-- Usuários podem ver dados do seu próprio cliente
DROP POLICY IF EXISTS "Users can view their client data" ON renum_clients;
CREATE POLICY "Users can view their client data" ON renum_clients
FOR SELECT USING (
    id IN (SELECT client_id FROM renum_users WHERE auth_user_id = auth.uid())
);

DROP POLICY IF EXISTS "Users can view their own user data" ON renum_users;
CREATE POLICY "Users can view their own user data" ON renum_users
FOR SELECT USING (auth_user_id = auth.uid());

DROP POLICY IF EXISTS "Users can view agents from their client" ON renum_agents;
CREATE POLICY "Users can view agents from their client" ON renum_agents
FOR SELECT USING (
    client_id IN (SELECT client_id FROM renum_users WHERE auth_user_id = auth.uid())
    OR created_by = auth.uid()
);

-- Políticas para administradores
DROP POLICY IF EXISTS "Admins can manage all data" ON renum_clients;
CREATE POLICY "Admins can manage all data" ON renum_clients
FOR ALL USING (
    auth.uid() IN (SELECT user_id FROM renum_admins WHERE is_active = true)
);

-- ========================================
-- PARTE 8: CRIAR FUNÇÕES ÚTEIS
-- ========================================

-- Função para verificar se um usuário tem acesso a um agente
CREATE OR REPLACE FUNCTION renum_user_has_agent_access(p_user_id UUID, p_agent_id UUID, p_min_permission TEXT DEFAULT 'view')
RETURNS BOOLEAN AS $$
DECLARE
    is_owner BOOLEAN;
    has_share BOOLEAN;
BEGIN
    -- Verificar se o usuário é o proprietário do agente
    SELECT EXISTS (
        SELECT 1 FROM renum_agents 
        WHERE id = p_agent_id AND created_by = p_user_id
    ) INTO is_owner;
    
    IF is_owner THEN
        RETURN TRUE;
    END IF;
    
    -- Verificar se o agente está compartilhado com o usuário
    SELECT EXISTS (
        SELECT 1 FROM renum_agent_shares 
        WHERE agent_id = p_agent_id 
        AND user_id = p_user_id
        AND (
            CASE 
                WHEN p_min_permission = 'view' THEN permission_level IN ('view', 'use', 'edit', 'admin')
                WHEN p_min_permission = 'use' THEN permission_level IN ('use', 'edit', 'admin')
                WHEN p_min_permission = 'edit' THEN permission_level IN ('edit', 'admin')
                WHEN p_min_permission = 'admin' THEN permission_level = 'admin'
                ELSE FALSE
            END
        )
        AND (expires_at IS NULL OR expires_at > now())
    ) INTO has_share;
    
    RETURN has_share;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ========================================
-- PARTE 9: RENOMEAR TABELA AGENT_SHARES PARA RENUM_AGENT_SHARES
-- ========================================

-- Verificar se a tabela agent_shares existe e renomeá-la
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'agent_shares') THEN
        ALTER TABLE IF EXISTS public.agent_shares RENAME TO renum_agent_shares_old;
        RAISE NOTICE 'Tabela agent_shares renomeada para renum_agent_shares_old';
    END IF;
END
$$;

-- ========================================
-- PARTE 10: VERIFICAR TABELAS CRIADAS
-- ========================================

-- Listar todas as tabelas com prefixo renum_
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'renum_%'
ORDER BY table_name;