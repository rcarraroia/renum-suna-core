-- Script para criar tabelas do painel administrativo no Supabase

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

-- Tabela de logs de auditoria
CREATE TABLE IF NOT EXISTS renum_audit_logs (
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

-- Função para atualizar o timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar o timestamp de updated_at
CREATE TRIGGER update_renum_admins_updated_at
BEFORE UPDATE ON renum_admins
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_renum_admin_credentials_updated_at
BEFORE UPDATE ON renum_admin_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_renum_system_settings_updated_at
BEFORE UPDATE ON renum_system_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Função para registrar ações de auditoria
CREATE OR REPLACE FUNCTION log_audit_event(
    p_event_type TEXT,
    p_entity_type TEXT,
    p_entity_id UUID,
    p_actor_id UUID,
    p_actor_type TEXT,
    p_details JSONB DEFAULT '{}'::jsonb,
    p_ip_address TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO renum_audit_logs (
        event_type,
        entity_type,
        entity_id,
        actor_id,
        actor_type,
        details,
        ip_address,
        user_agent
    ) VALUES (
        p_event_type,
        p_entity_type,
        p_entity_id,
        p_actor_id,
        p_actor_type,
        p_details,
        p_ip_address,
        p_user_agent
    ) RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Função para executar SQL (para uso do MCP)
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN (SELECT jsonb_agg(t) FROM (EXECUTE sql) t);
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('error', SQLERRM);
END;
$$;

-- Função para listar tabelas (para uso do MCP)
CREATE OR REPLACE FUNCTION list_tables()
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN (
        SELECT jsonb_agg(table_name)
        FROM information_schema.tables
        WHERE table_schema = 'public'
    );
END;
$$;

-- Políticas RLS para as tabelas
ALTER TABLE renum_admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_admin_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE renum_audit_logs ENABLE ROW LEVEL SECURITY;

-- Política para renum_admins (apenas superadmin pode gerenciar outros admins)
CREATE POLICY admin_superadmin_policy ON renum_admins
    USING (
        (SELECT role FROM renum_admins WHERE user_id = auth.uid()) = 'superadmin'
        OR user_id = auth.uid()
    );

-- Política para renum_admin_credentials (apenas o próprio admin pode ver suas credenciais)
CREATE POLICY admin_credentials_policy ON renum_admin_credentials
    USING (
        admin_id IN (SELECT id FROM renum_admins WHERE user_id = auth.uid())
    );

-- Política para renum_system_settings (todos os admins podem ver, apenas superadmin pode modificar)
CREATE POLICY system_settings_read_policy ON renum_system_settings
    FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM renum_admins WHERE user_id = auth.uid())
    );

CREATE POLICY system_settings_write_policy ON renum_system_settings
    FOR ALL
    USING (
        (SELECT role FROM renum_admins WHERE user_id = auth.uid()) = 'superadmin'
    );

-- Política para renum_audit_logs (todos os admins podem ver)
CREATE POLICY audit_logs_policy ON renum_audit_logs
    FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM renum_admins WHERE user_id = auth.uid())
    );

-- Inserir um superadmin inicial (substitua os valores conforme necessário)
-- Nota: O usuário deve ser criado primeiro no auth.users
-- INSERT INTO renum_admins (user_id, name, email, role)
-- VALUES ('SUBSTITUA_COM_USER_ID', 'Admin Principal', 'admin@exemplo.com', 'superadmin');