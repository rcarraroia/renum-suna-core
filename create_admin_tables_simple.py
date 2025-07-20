from supabase import create_client

# Criar cliente Supabase
supabase_url = "https://uxxvoicxhkakpguvavba.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"
client = create_client(supabase_url, supabase_key)

# Comandos SQL para criar as tabelas
create_tables_commands = [
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
    )
    """,
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
    )
    """,
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
    )
    """,
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
    )
    """
]

# Executar cada comando
for i, command in enumerate(create_tables_commands):
    try:
        print(f"Executando comando {i+1}/{len(create_tables_commands)}...")
        result = client.rpc("exec_sql", {"sql": command}).execute()
        print(f"Resultado: {result.data}")
    except Exception as e:
        print(f"Erro ao executar comando: {e}")

print("Tabelas criadas com sucesso!")