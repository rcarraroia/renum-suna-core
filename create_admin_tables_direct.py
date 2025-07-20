#!/usr/bin/env python3
"""
Script para criar tabelas administrativas diretamente no Supabase
"""

import os
from supabase import create_client

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

def create_admin_tables():
    """Cria as tabelas administrativas no Supabase"""
    
    # Criar cliente Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # SQL para criar as tabelas administrativas
    sql_commands = [
        # Tabela de administradores
        """
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
        """,
        
        # Tabela de credenciais administrativas
        """
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
        """,
        
        # Tabela de configurações do sistema
        """
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
        """,
        
        # Tabela de logs de auditoria
        """
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
        """,
        
        # Função para atualizar o timestamp de updated_at
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        
        # Triggers para atualizar o timestamp de updated_at
        """
        DROP TRIGGER IF EXISTS update_renum_admins_updated_at ON renum_admins;
        CREATE TRIGGER update_renum_admins_updated_at
        BEFORE UPDATE ON renum_admins
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """,
        
        """
        DROP TRIGGER IF EXISTS update_renum_admin_credentials_updated_at ON renum_admin_credentials;
        CREATE TRIGGER update_renum_admin_credentials_updated_at
        BEFORE UPDATE ON renum_admin_credentials
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """,
        
        """
        DROP TRIGGER IF EXISTS update_renum_system_settings_updated_at ON renum_system_settings;
        CREATE TRIGGER update_renum_system_settings_updated_at
        BEFORE UPDATE ON renum_system_settings
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """,
        
        # Função para registrar ações de auditoria
        """
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
        """,
        
        # Habilitar RLS
        """
        ALTER TABLE renum_admins ENABLE ROW LEVEL SECURITY;
        ALTER TABLE renum_admin_credentials ENABLE ROW LEVEL SECURITY;
        ALTER TABLE renum_system_settings ENABLE ROW LEVEL SECURITY;
        ALTER TABLE renum_audit_logs ENABLE ROW LEVEL SECURITY;
        """,
        
        # Políticas RLS
        """
        DROP POLICY IF EXISTS admin_superadmin_policy ON renum_admins;
        CREATE POLICY admin_superadmin_policy ON renum_admins
            USING (
                (SELECT role FROM renum_admins WHERE user_id = auth.uid()) = 'superadmin'
                OR user_id = auth.uid()
            );
        """,
        
        """
        DROP POLICY IF EXISTS admin_credentials_policy ON renum_admin_credentials;
        CREATE POLICY admin_credentials_policy ON renum_admin_credentials
            USING (
                admin_id IN (SELECT id FROM renum_admins WHERE user_id = auth.uid())
            );
        """,
        
        """
        DROP POLICY IF EXISTS system_settings_read_policy ON renum_system_settings;
        CREATE POLICY system_settings_read_policy ON renum_system_settings
            FOR SELECT
            USING (
                EXISTS (SELECT 1 FROM renum_admins WHERE user_id = auth.uid())
            );
        """,
        
        """
        DROP POLICY IF EXISTS system_settings_write_policy ON renum_system_settings;
        CREATE POLICY system_settings_write_policy ON renum_system_settings
            FOR ALL
            USING (
                (SELECT role FROM renum_admins WHERE user_id = auth.uid()) = 'superadmin'
            );
        """,
        
        """
        DROP POLICY IF EXISTS audit_logs_policy ON renum_audit_logs;
        CREATE POLICY audit_logs_policy ON renum_audit_logs
            FOR SELECT
            USING (
                EXISTS (SELECT 1 FROM renum_admins WHERE user_id = auth.uid())
            );
        """
    ]
    
    # Executar cada comando SQL
    for i, sql in enumerate(sql_commands):
        try:
            print(f"Executando comando {i+1}/{len(sql_commands)}...")
            result = supabase.rpc('exec_sql', {'sql': sql.strip()}).execute()
            
            if hasattr(result, 'error') and result.error:
                print(f"Erro no comando {i+1}: {result.error}")
            else:
                print(f"Comando {i+1} executado com sucesso!")
                
        except Exception as e:
            print(f"Erro ao executar comando {i+1}: {e}")
    
    print("Processo concluído!")

def check_tables():
    """Verifica se as tabelas foram criadas"""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        result = supabase.rpc('exec_sql', {
            'sql': """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'renum_%'
            ORDER BY table_name;
            """
        }).execute()
        
        print("Tabelas com prefixo 'renum_' encontradas:")
        if result.data:
            for table in result.data:
                print(f"  - {table['table_name']}")
        else:
            print("  Nenhuma tabela encontrada")
            
    except Exception as e:
        print(f"Erro ao verificar tabelas: {e}")

if __name__ == "__main__":
    print("Criando tabelas administrativas...")
    create_admin_tables()
    print("\nVerificando tabelas criadas...")
    check_tables()