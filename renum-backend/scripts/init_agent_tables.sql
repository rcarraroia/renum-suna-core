-- Script para inicializar as tabelas de agentes no Supabase
-- Tabela de agentes
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    client_id UUID NOT NULL REFERENCES clients(id),
    configuration JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    knowledge_base_ids UUID[] DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela de execuções de agentes
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    status TEXT NOT NULL DEFAULT 'pending',
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    tokens_used INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}',
    context_used JSONB,
    tools_used TEXT[],
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_agents_client_id ON agents(client_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_by ON agents(created_by);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_user_id ON agent_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_client_id ON agent_executions(client_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started_at ON agent_executions(started_at);

-- Índice GIN para busca em arrays de knowledge_base_ids
CREATE INDEX IF NOT EXISTS idx_agents_knowledge_base_ids ON agents USING GIN (knowledge_base_ids);

-- Triggers para atualizar o campo updated_at automaticamente
CREATE TRIGGER update_agents_updated_at
BEFORE UPDATE ON agents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_executions_updated_at
BEFORE UPDATE ON agent_executions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Políticas de segurança RLS (Row Level Security)
-- Habilitar RLS para todas as tabelas
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;

-- Políticas para agentes
CREATE POLICY agents_select_policy ON agents
    FOR SELECT
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agents.client_id OR role = 'admin'
        )
    );

CREATE POLICY agents_insert_policy ON agents
    FOR INSERT
    WITH CHECK (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agents.client_id OR role = 'admin'
        )
    );

CREATE POLICY agents_update_policy ON agents
    FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agents.client_id OR role = 'admin'
        )
    );

CREATE POLICY agents_delete_policy ON agents
    FOR DELETE
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agents.client_id OR role = 'admin'
        )
    );

-- Políticas para execuções de agentes
CREATE POLICY agent_executions_select_policy ON agent_executions
    FOR SELECT
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agent_executions.client_id OR role = 'admin'
        )
    );

CREATE POLICY agent_executions_insert_policy ON agent_executions
    FOR INSERT
    WITH CHECK (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agent_executions.client_id OR role = 'admin'
        )
    );

CREATE POLICY agent_executions_update_policy ON agent_executions
    FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agent_executions.client_id OR role = 'admin'
        )
    );

CREATE POLICY agent_executions_delete_policy ON agent_executions
    FOR DELETE
    USING (
        auth.uid() IN (
            SELECT id FROM users WHERE client_id = agent_executions.client_id OR role = 'admin'
        )
    );