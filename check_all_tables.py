from supabase import create_client

# Criar cliente Supabase
supabase_url = "https://uxxvoicxhkakpguvavba.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"
client = create_client(supabase_url, supabase_key)

print("=== VERIFICAÇÃO COMPLETA DO BANCO DE DADOS ===\n")

# Listar todas as tabelas
try:
    result = client.rpc("exec_sql", {"sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"}).execute()
    
    if result.data and not isinstance(result.data, dict):
        print(f"Total de tabelas encontradas: {len(result.data)}")
        print("\nTabelas existentes:")
        
        renum_tables = []
        other_tables = []
        
        for table in result.data:
            table_name = table.get('table_name', table)
            if str(table_name).startswith('renum_'):
                renum_tables.append(table_name)
            else:
                other_tables.append(table_name)
        
        print(f"\n--- TABELAS COM PREFIXO 'renum_' ({len(renum_tables)}) ---")
        for table in renum_tables:
            print(f"  ✓ {table}")
        
        print(f"\n--- OUTRAS TABELAS ({len(other_tables)}) ---")
        for table in other_tables:
            print(f"  • {table}")
            
    else:
        print("Erro ao listar tabelas ou resultado vazio")
        print(f"Resultado: {result.data}")
        
except Exception as e:
    print(f"Erro ao listar tabelas: {e}")

# Verificar tabelas específicas que esperamos existir
expected_tables = [
    # Tabelas do sistema principal
    "renum_clients", "renum_users", "renum_agents", "renum_threads", "renum_messages",
    # Tabelas do módulo RAG (sem prefixo - problema!)
    "knowledge_bases", "knowledge_collections", "documents", "document_chunks",
    # Tabelas do compartilhamento de agentes
    "renum_agent_shares", "agent_shares",
    # Tabelas do painel administrativo
    "renum_admins", "renum_admin_credentials", "renum_system_settings", "renum_audit_logs"
]

print(f"\n=== VERIFICAÇÃO DE TABELAS ESPECÍFICAS ===")
for table in expected_tables:
    try:
        result = client.from_(table).select("*", count="exact").limit(1).execute()
        print(f"  ✓ {table}: {result.count} registros")
    except Exception as e:
        if "does not exist" in str(e):
            print(f"  ✗ {table}: NÃO EXISTE")
        else:
            print(f"  ? {table}: ERRO - {e}")

print(f"\n=== ANÁLISE CONCLUÍDA ===")