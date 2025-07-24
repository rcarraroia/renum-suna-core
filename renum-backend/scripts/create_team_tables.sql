-- Script para criação das tabelas do sistema de Equipes de Agentes
-- Este script deve ser executado no banco de dados Supabase

-- Tabela principal de equipes
CREATE TABLE IF NOT EXISTS renum_agent_teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_ids JSONB NOT NULL, -- Array de agent_ids que compõem a equipe
    workflow_definition JSONB NOT NULL, -- JSON/DSL que descreve a orquestração
    user_api_keys JSONB DEFAULT '{}', -- API keys personalizadas do usuário
    team_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Execuções de equipe
CREATE TABLE IF NOT EXISTS renum_team_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES renum_agent_teams(team_id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    execution_plan JSONB, -- Plano de execução gerado pelo workflow_definition
    shared_context JSONB DEFAULT '{}', -- Context object compartilhado
    initial_prompt TEXT,
    final_result JSONB,
    error_message TEXT,
    cost_metrics JSONB DEFAULT '{}', -- Métricas de custo por agente individual
    usage_metrics JSONB DEFAULT '{}', -- Consumo de modelos IA por agente
    api_keys_used JSONB DEFAULT '{}', -- Registro das API keys utilizadas
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Log de execução de agentes individuais na equipe
CREATE TABLE IF NOT EXISTS renum_team_agent_executions (
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL, -- ID do agente no Suna Core
    suna_agent_run_id UUID, -- ID da execução no Backend Suna
    step_order INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    input_data JSONB,
    output_data JSONB,
    context_snapshot JSONB, -- Snapshot do contexto no momento da execução
    error_message TEXT,
    individual_cost_metrics JSONB DEFAULT '{}', -- Custo específico deste agente
    individual_usage_metrics JSONB DEFAULT '{}', -- Uso específico deste agente
    api_keys_snapshot JSONB DEFAULT '{}', -- API keys usadas por este agente
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (execution_id, agent_id)
);

-- Log de mensagens entre agentes
CREATE TABLE IF NOT EXISTS renum_team_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    from_agent_id VARCHAR(255), -- ID do agente no Suna Core
    to_agent_id VARCHAR(255), -- NULL para broadcast
    message_type VARCHAR(50) NOT NULL, -- 'info', 'request', 'response', 'error', 'context_update'
    content JSONB NOT NULL,
    requires_response BOOLEAN DEFAULT false,
    response_timeout INTEGER,
    response_message_id UUID REFERENCES renum_team_messages(message_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contexto compartilhado (backup/auditoria - dados principais no Redis)
CREATE TABLE IF NOT EXISTS renum_team_context_snapshots (
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context_data JSONB NOT NULL, -- Context object completo
    version INTEGER DEFAULT 1,
    created_by_agent VARCHAR(255), -- ID do agente no Suna Core
    PRIMARY KEY (execution_id, snapshot_at)
);

-- Tabela para logging de uso de modelos IA (preparação para billing nativo)
CREATE TABLE IF NOT EXISTS renum_ai_usage_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    execution_id UUID REFERENCES renum_team_executions(execution_id),
    agent_id VARCHAR(255), -- ID do agente no Suna Core
    model_provider VARCHAR(100), -- 'openai', 'anthropic', 'custom', etc.
    model_name VARCHAR(100),
    api_key_type VARCHAR(50), -- 'user_provided', 'renum_native' (futuro)
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    request_data JSONB, -- Dados da requisição para auditoria
    response_data JSONB, -- Dados da resposta para auditoria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para armazenar API keys dos usuários (criptografadas)
CREATE TABLE IF NOT EXISTS renum_user_api_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    service_name VARCHAR(100) NOT NULL, -- 'openai', 'anthropic', etc.
    encrypted_key TEXT NOT NULL, -- Chave criptografada
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, service_name)
);

-- Políticas RLS para segurança

-- Política para renum_agent_teams
ALTER TABLE renum_agent_teams ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_agent_teams_user_policy ON renum_agent_teams
    FOR ALL
    USING (user_id = auth.uid());

-- Política para renum_team_executions
ALTER TABLE renum_team_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_team_executions_user_policy ON renum_team_executions
    FOR ALL
    USING (user_id = auth.uid());

-- Política para renum_team_agent_executions
ALTER TABLE renum_team_agent_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_team_agent_executions_user_policy ON renum_team_agent_executions
    FOR ALL
    USING (
        execution_id IN (
            SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
        )
    );

-- Política para renum_team_messages
ALTER TABLE renum_team_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_team_messages_user_policy ON renum_team_messages
    FOR ALL
    USING (
        execution_id IN (
            SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
        )
    );

-- Política para renum_team_context_snapshots
ALTER TABLE renum_team_context_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_team_context_snapshots_user_policy ON renum_team_context_snapshots
    FOR ALL
    USING (
        execution_id IN (
            SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
        )
    );

-- Política para renum_ai_usage_logs
ALTER TABLE renum_ai_usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_ai_usage_logs_user_policy ON renum_ai_usage_logs
    FOR ALL
    USING (user_id = auth.uid());

-- Política para renum_user_api_keys
ALTER TABLE renum_user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY renum_user_api_keys_user_policy ON renum_user_api_keys
    FOR ALL
    USING (user_id = auth.uid());

-- Índices para melhorar performance

-- Índices para renum_agent_teams
CREATE INDEX IF NOT EXISTS idx_renum_agent_teams_user_id ON renum_agent_teams(user_id);

-- Índices para renum_team_executions
CREATE INDEX IF NOT EXISTS idx_renum_team_executions_team_id ON renum_team_executions(team_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_executions_user_id ON renum_team_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_executions_status ON renum_team_executions(status);
CREATE INDEX IF NOT EXISTS idx_renum_team_executions_created_at ON renum_team_executions(created_at);

-- Índices para renum_team_agent_executions
CREATE INDEX IF NOT EXISTS idx_renum_team_agent_executions_execution_id ON renum_team_agent_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_agent_executions_agent_id ON renum_team_agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_agent_executions_status ON renum_team_agent_executions(status);

-- Índices para renum_team_messages
CREATE INDEX IF NOT EXISTS idx_renum_team_messages_execution_id ON renum_team_messages(execution_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_messages_from_agent_id ON renum_team_messages(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_messages_to_agent_id ON renum_team_messages(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_renum_team_messages_created_at ON renum_team_messages(created_at);

-- Índices para renum_ai_usage_logs
CREATE INDEX IF NOT EXISTS idx_renum_ai_usage_logs_user_id ON renum_ai_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_ai_usage_logs_execution_id ON renum_ai_usage_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_renum_ai_usage_logs_created_at ON renum_ai_usage_logs(created_at);

-- Índices para renum_user_api_keys
CREATE INDEX IF NOT EXISTS idx_renum_user_api_keys_user_id ON renum_user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_user_api_keys_service_name ON renum_user_api_keys(service_name);