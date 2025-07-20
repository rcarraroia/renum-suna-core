import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    exit(1)

# Headers for Supabase REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def get_all_tables():
    """Get all tables from the database"""
    query = """
    SELECT 
        table_name 
    FROM 
        information_schema.tables 
    WHERE 
        table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    ORDER BY 
        table_name;
    """
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": query}
    )
    
    if response.status_code != 200:
        print(f"Error fetching tables: {response.text}")
        return []
    
    return response.json()

def check_renum_prefixes():
    """Check which tables have the 'renum_' prefix"""
    tables = get_all_tables()
    
    renum_tables = []
    non_renum_tables = []
    
    for table in tables:
        table_name = table['table_name']
        if table_name.startswith('renum_'):
            renum_tables.append(table_name)
        else:
            # Exclude Supabase system tables
            if not table_name.startswith(('pg_', 'auth.', 'storage.', '_')):
                non_renum_tables.append(table_name)
    
    print("\n=== TABLES WITH 'renum_' PREFIX ===\n")
    for table in sorted(renum_tables):
        print(f"✅ {table}")
    
    print("\n=== TABLES WITHOUT 'renum_' PREFIX ===\n")
    for table in sorted(non_renum_tables):
        print(f"⚠️ {table}")
    
    print(f"\nTotal tables with 'renum_' prefix: {len(renum_tables)}")
    print(f"Total tables without 'renum_' prefix: {len(non_renum_tables)}")

if __name__ == "__main__":
    print("Checking tables for 'renum_' prefix...\n")
    check_renum_prefixes()