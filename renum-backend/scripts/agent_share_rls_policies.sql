-- Script para criar tabela de compartilhamento de agentes e políticas RLS no Supabase

-- Criar tabela de compartilhamento de agentes se não existir
CREATE TABLE IF NOT EXISTS public.agent_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    permission_level TEXT NOT NULL DEFAULT 'view',
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(agent_id, user_id)
);

-- Adicionar comentários à tabela e colunas
COMMENT ON TABLE public.agent_shares IS 'Tabela para armazenar compartilhamentos de agentes entre usuários';
COMMENT ON COLUMN public.agent_shares.id IS 'ID único do compartilhamento';
COMMENT ON COLUMN public.agent_shares.agent_id IS 'ID do agente compartilhado';
COMMENT ON COLUMN public.agent_shares.user_id IS 'ID do usuário com quem o agente é compartilhado';
COMMENT ON COLUMN public.agent_shares.client_id IS 'ID do cliente do usuário com quem o agente é compartilhado';
COMMENT ON COLUMN public.agent_shares.permission_level IS 'Nível de permissão concedido (view, use, edit, admin)';
COMMENT ON COLUMN public.agent_shares.created_by IS 'ID do usuário que criou o compartilhamento';
COMMENT ON COLUMN public.agent_shares.created_at IS 'Data de criação do compartilhamento';
COMMENT ON COLUMN public.agent_shares.updated_at IS 'Data de última atualização do compartilhamento';
COMMENT ON COLUMN public.agent_shares.expires_at IS 'Data de expiração do compartilhamento (opcional)';
COMMENT ON COLUMN public.agent_shares.metadata IS 'Metadados adicionais do compartilhamento';

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_agent_shares_agent_id ON public.agent_shares(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_user_id ON public.agent_shares(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_client_id ON public.agent_shares(client_id);
CREATE INDEX IF NOT EXISTS idx_agent_shares_created_by ON public.agent_shares(created_by);
CREATE INDEX IF NOT EXISTS idx_agent_shares_expires_at ON public.agent_shares(expires_at);

-- Criar trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION public.update_agent_shares_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_agent_shares_updated_at_trigger ON public.agent_shares;
CREATE TRIGGER update_agent_shares_updated_at_trigger
BEFORE UPDATE ON public.agent_shares
FOR EACH ROW
EXECUTE FUNCTION public.update_agent_shares_updated_at();

-- Habilitar RLS na tabela
ALTER TABLE public.agent_shares ENABLE ROW LEVEL SECURITY;

-- Remover políticas existentes (se houver)
DROP POLICY IF EXISTS "Usuários podem ver seus próprios compartilhamentos" ON public.agent_shares;
DROP POLICY IF EXISTS "Usuários podem ver compartilhamentos de seus agentes" ON public.agent_shares;
DROP POLICY IF EXISTS "Usuários podem criar compartilhamentos para seus agentes" ON public.agent_shares;
DROP POLICY IF EXISTS "Usuários podem atualizar compartilhamentos de seus agentes" ON public.agent_shares;
DROP POLICY IF EXISTS "Usuários podem excluir compartilhamentos de seus agentes" ON public.agent_shares;
DROP POLICY IF EXISTS "Administradores podem gerenciar todos os compartilhamentos" ON public.agent_shares;

-- Criar políticas RLS

-- Política para visualização: usuários podem ver compartilhamentos onde são o destinatário ou o criador
CREATE POLICY "Usuários podem ver seus próprios compartilhamentos"
ON public.agent_shares
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
ON public.agent_shares
FOR INSERT
WITH CHECK (
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    ) OR
    auth.uid() IN (
        SELECT user_id FROM public.agent_shares 
        WHERE agent_id = NEW.agent_id AND permission_level = 'admin'
    )
);

-- Política para atualização: usuários só podem atualizar compartilhamentos que criaram ou de agentes que possuem
CREATE POLICY "Usuários podem atualizar compartilhamentos de seus agentes"
ON public.agent_shares
FOR UPDATE
USING (
    auth.uid() = created_by OR
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    )
);

-- Política para exclusão: usuários só podem excluir compartilhamentos que criaram ou de agentes que possuem
CREATE POLICY "Usuários podem excluir compartilhamentos de seus agentes"
ON public.agent_shares
FOR DELETE
USING (
    auth.uid() = created_by OR
    auth.uid() IN (
        SELECT created_by FROM public.agents WHERE id = agent_id
    )
);

-- Política para administradores: podem gerenciar todos os compartilhamentos
CREATE POLICY "Administradores podem gerenciar todos os compartilhamentos"
ON public.agent_shares
FOR ALL
USING (
    auth.uid() IN (
        SELECT user_id FROM public.user_roles WHERE role = 'admin'
    )
);

-- Atualizar políticas RLS na tabela de agentes para considerar compartilhamentos

-- Remover políticas existentes (se houver)
DROP POLICY IF EXISTS "Usuários podem ver agentes compartilhados com eles" ON public.agents;
DROP POLICY IF EXISTS "Usuários com permissão podem editar agentes compartilhados" ON public.agents;

-- Política para permitir que usuários vejam agentes compartilhados com eles
CREATE POLICY "Usuários podem ver agentes compartilhados com eles"
ON public.agents
FOR SELECT
USING (
    auth.uid() IN (
        SELECT user_id FROM public.agent_shares 
        WHERE agent_id = id AND (expires_at IS NULL OR expires_at > now())
    )
);

-- Política para permitir que usuários com permissão de edição possam atualizar agentes compartilhados
CREATE POLICY "Usuários com permissão podem editar agentes compartilhados"
ON public.agents
FOR UPDATE
USING (
    auth.uid() IN (
        SELECT user_id FROM public.agent_shares 
        WHERE agent_id = id 
        AND permission_level IN ('edit', 'admin')
        AND (expires_at IS NULL OR expires_at > now())
    )
);

-- Função para verificar se um usuário tem acesso a um agente (próprio ou compartilhado)
CREATE OR REPLACE FUNCTION public.user_has_agent_access(p_user_id UUID, p_agent_id UUID, p_min_permission TEXT DEFAULT 'view')
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
        SELECT 1 FROM public.agent_shares 
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