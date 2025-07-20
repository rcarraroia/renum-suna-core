-- Script para criar as tabelas do sistema Renum no banco de dados Supabase
-- Todas as tabelas usam o prefixo 'renum_' para distingui-las das tabelas do sistema Suna

-- Criar extensão uuid-ossp se ainda não existir
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de compartilhamento de agentes
CREATE TABLE IF NOT EXISTS public.renum_agent_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL,
    permission_level TEXT NOT NULL DEFAULT 'view',
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(agent_id, user_id)
);

-- Adicionar comentários à tabela e colunas
COMMENT ON TABLE public.renum_agent_shares IS 'Tabela para armazenar compartilhamentos de agentes entre usuários (Interface Renum)';
COMMENT ON COLUMN public.renum_agent_shares.id IS 'ID único do compartilhamento';
COMMENT ON COLUMN public.renum_agent_shares.agent_id IS 'ID do agente compartilhado';
COMMENT ON COLUMN public.renum_agent_shares.user_id IS 'ID do usuário com quem o agente é compartilhado';
COMMENT ON COLUMN public.renum_agent_shares.client_id IS 'ID do cliente do usuário com quem o agente é compartilhado';
COMMENT ON COLUMN public.renum_agent_shares.permission_level IS 'Nível de permissão concedido (view, use, edit, admin)';
COMMENT ON COLUMN public.renum_agent_shares.created_by IS 'ID do usuário que criou o compartilhamento';
COMMENT ON COLUMN public.renum_agent_shares.created_at IS 'Data de criação do compartilhamento';
COMMENT ON COLUMN public.renum_agent_shares.updated_at IS 'Data de última atualização do compartilhamento';
COMMENT ON COLUMN public.renum_agent_shares.expires_at IS 'Data de expiração do compartilhamento (opcional)';
COMMENT ON COLUMN public.renum_agent_shares.metadata IS 'Metadados adicionais do compartilhamento';

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_agent_id ON public.renum_agent_shares(agent_id);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_user_id ON public.renum_agent_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_client_id ON public.renum_agent_shares(client_id);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_created_by ON public.renum_agent_shares(created_by);
CREATE INDEX IF NOT EXISTS idx_renum_agent_shares_expires_at ON public.renum_agent_shares(expires_at);

-- Criar trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION public.update_renum_agent_shares_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_renum_agent_shares_updated_at_trigger ON public.renum_agent_shares;
CREATE TRIGGER update_renum_agent_shares_updated_at_trigger
BEFORE UPDATE ON public.renum_agent_shares
FOR EACH ROW
EXECUTE FUNCTION public.update_renum_agent_shares_updated_at();

-- Habilitar RLS na tabela
ALTER TABLE public.renum_agent_shares ENABLE ROW LEVEL SECURITY;

-- Remover políticas existentes (se houver)
DROP POLICY IF EXISTS "Usuários podem ver seus próprios compartilhamentos" ON public.renum_agent_shares;
DROP POLICY IF EXISTS "Usuários podem criar compartilhamentos para seus agentes" ON public.renum_agent_shares;
DROP POLICY IF EXISTS "Usuários podem atualizar compartilhamentos de seus agentes" ON public.renum_agent_shares;
DROP POLICY IF EXISTS "Usuários podem excluir compartilhamentos de seus agentes" ON public.renum_agent_shares;
DROP POLICY IF EXISTS "Administradores podem gerenciar todos os compartilhamentos" ON public.renum_agent_shares;

-- Criar políticas RLS

-- Política para visualização: usuários podem ver compartilhamentos onde são o destinatário ou o criador
CREATE POLICY "Usuários podem ver seus próprios compartilhamentos"
ON public.renum_agent_shares
FOR SELECT
USING (
    auth.uid() = user_id OR 
    auth.uid() = created_by OR
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    )
);

-- Política para criação: usuários só podem criar compartilhamentos para agentes que possuem ou têm permissão admin
CREATE POLICY "Usuários podem criar compartilhamentos para seus agentes"
ON public.renum_agent_shares
FOR INSERT
WITH CHECK (
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    ) OR
    auth.uid() IN (
        SELECT user_id FROM public.renum_agent_shares 
        WHERE agent_id = agent_id AND permission_level = 'admin'
    )
);

-- Política para atualização: usuários só podem atualizar compartilhamentos que criaram ou de agentes que possuem
CREATE POLICY "Usuários podem atualizar compartilhamentos de seus agentes"
ON public.renum_agent_shares
FOR UPDATE
USING (
    auth.uid() = created_by OR
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    )
);

-- Política para exclusão: usuários só podem excluir compartilhamentos que criaram ou de agentes que possuem
CREATE POLICY "Usuários podem excluir compartilhamentos de seus agentes"
ON public.renum_agent_shares
FOR DELETE
USING (
    auth.uid() = created_by OR
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    )
);

-- Tabela de configurações da interface Renum
CREATE TABLE IF NOT EXISTS public.renum_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    UNIQUE(client_id, setting_key)
);

COMMENT ON TABLE public.renum_settings IS 'Configurações específicas da interface Renum';

-- Tabela de métricas e estatísticas da interface Renum
CREATE TABLE IF NOT EXISTS public.renum_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    metric_type TEXT NOT NULL,
    metric_data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    user_id UUID REFERENCES auth.users(id)
);

COMMENT ON TABLE public.renum_metrics IS 'Métricas e estatísticas coletadas pela interface Renum';

-- Tabela de auditoria da interface Renum
CREATE TABLE IF NOT EXISTS public.renum_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    client_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE public.renum_audit_logs IS 'Logs de auditoria para ações realizadas na interface Renum';

-- Função para verificar se um usuário tem acesso a um agente (próprio ou compartilhado)
CREATE OR REPLACE FUNCTION public.renum_user_has_agent_access(p_user_id UUID, p_agent_id UUID, p_min_permission TEXT DEFAULT 'view')
RETURNS BOOLEAN AS $$
DECLARE
    is_owner BOOLEAN;
    has_share BOOLEAN;
BEGIN
    -- Verificar se o usuário é o proprietário do agente
    SELECT EXISTS (
        SELECT 1 FROM public.agents 
        WHERE id = p_agent_id AND created_by = p_user_id
    ) INTO is_owner;
    
    IF is_owner THEN
        RETURN TRUE;
    END IF;
    
    -- Verificar se o agente está compartilhado com o usuário com o nível de permissão adequado
    SELECT EXISTS (
        SELECT 1 FROM public.renum_agent_shares 
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