-- Script para criar a tabela de frases da página inicial com prefixo renum
CREATE TABLE IF NOT EXISTS public.renum_homepage_phrases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Adicionar comentários à tabela e colunas
COMMENT ON TABLE public.renum_homepage_phrases IS 'Tabela para armazenar frases exibidas com efeito de máquina de escrever na página inicial';
COMMENT ON COLUMN public.renum_homepage_phrases.id IS 'ID único da frase';
COMMENT ON COLUMN public.renum_homepage_phrases.text IS 'Texto da frase';
COMMENT ON COLUMN public.renum_homepage_phrases.display_order IS 'Ordem de exibição das frases';
COMMENT ON COLUMN public.renum_homepage_phrases.is_active IS 'Indica se a frase está ativa para exibição';
COMMENT ON COLUMN public.renum_homepage_phrases.created_at IS 'Data de criação da frase';
COMMENT ON COLUMN public.renum_homepage_phrases.updated_at IS 'Data de última atualização da frase';

-- Criar trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION public.update_renum_homepage_phrases_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_renum_homepage_phrases_updated_at_trigger ON public.renum_homepage_phrases;
CREATE TRIGGER update_renum_homepage_phrases_updated_at_trigger
BEFORE UPDATE ON public.renum_homepage_phrases
FOR EACH ROW
EXECUTE FUNCTION public.update_renum_homepage_phrases_updated_at();

-- Habilitar RLS na tabela
ALTER TABLE public.renum_homepage_phrases ENABLE ROW LEVEL SECURITY;

-- Políticas RLS
-- Política para administradores: podem gerenciar todas as frases
CREATE POLICY "Administradores podem gerenciar todas as frases"
ON public.renum_homepage_phrases
FOR ALL
USING (
    auth.uid() IN (SELECT user_id FROM renum_admins WHERE is_active = true)
);

-- Política para usuários: podem visualizar frases ativas
CREATE POLICY "Usuários podem visualizar frases ativas"
ON public.renum_homepage_phrases
FOR SELECT
USING (
    is_active = true
);

-- Inserir algumas frases iniciais
INSERT INTO public.renum_homepage_phrases (text, display_order, is_active)
VALUES 
    ('Crie agentes de IA personalizados para seu negócio', 0, true),
    ('Automatize tarefas repetitivas com inteligência artificial', 1, true),
    ('Conecte seus dados e conhecimento aos modelos de IA mais avançados', 2, true),
    ('Transforme a experiência dos seus clientes com atendimento inteligente', 3, true),
    ('Potencialize sua produtividade com assistentes de IA especializados', 4, true);