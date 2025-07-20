from supabase import create_client

# Criar cliente Supabase
supabase_url = "https://uxxvoicxhkakpguvavba.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"
client = create_client(supabase_url, supabase_key)

# Verificar tabelas existentes
try:
    result = client.rpc("exec_sql", {"sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"}).execute()
    print("Tabelas existentes:")
    for table in result.data:
        print(f"- {table}")
except Exception as e:
    print(f"Erro ao listar tabelas: {e}")

# Verificar se as tabelas do painel administrativo existem
admin_tables = ["renum_admins", "renum_admin_credentials", "renum_system_settings", "renum_audit_logs"]
for table in admin_tables:
    try:
        result = client.from_(table).select("*", count="exact").limit(1).execute()
        print(f"Tabela {table}: {result.count} registros")
    except Exception as e:
        print(f"Erro ao verificar tabela {table}: {e}")