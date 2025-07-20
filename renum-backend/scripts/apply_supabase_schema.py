"""
Script para aplicar o esquema de compartilhamento de agentes no Supabase.
Este script usa o cliente Supabase que já foi testado e funcionou anteriormente.
"""

import os
import sys
from dotenv import load_dotenv

# Tente importar o cliente Supabase da aplicação
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from app.core.supabase_client import get_supabase_client
    print("Usando cliente Supabase da aplicação")
    supabase_client_available = True
except ImportError:
    print("Cliente Supabase da aplicação não encontrado, usando implementação alternativa")
    supabase_client_available = False
    
    # Implementação alternativa
    import httpx
    from supabase import create_client, Client

    def get_supabase_client():
        """Obtém um cliente Supabase usando variáveis de ambiente."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar definidos no ambiente")
        
        return create_client(url, key)

def load_sql_file(file_path):
    """Carrega um arquivo SQL."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo SQL: {e}")
        sys.exit(1)

def execute_sql_statements(sql_content):
    """Executa comandos SQL no Supabase."""
    try:
        # Obter cliente Supabase
        supabase = get_supabase_client()
        
        # Dividir o conteúdo SQL em comandos individuais
        # Isso é uma simplificação e pode não funcionar para todos os casos
        statements = sql_content.split(';')
        
        success_count = 0
        error_count = 0
        
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
                
            try:
                print(f"Executando: {statement[:100]}...")  # Mostrar apenas os primeiros 100 caracteres
                
                # Adicionar ponto e vírgula de volta
                statement = statement + ';'
                
                # Executar o comando SQL
                result = supabase.rpc('execute_sql', {'query': statement}).execute()
                
                # Verificar resultado
                if hasattr(result, 'error') and result.error:
                    print(f"Erro: {result.error}")
                    error_count += 1
                else:
                    print("Sucesso!")
                    success_count += 1
                    
            except Exception as e:
                print(f"Erro ao executar comando: {e}")
                error_count += 1
        
        print(f"\nResumo: {success_count} comandos executados com sucesso, {error_count} erros")
        return error_count == 0
        
    except Exception as e:
        print(f"Erro ao conectar ao Supabase: {e}")
        return False

def main():
    """Função principal."""
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Variáveis de ambiente carregadas de {env_path}")
    else:
        print("Arquivo .env não encontrado, usando variáveis de ambiente existentes")
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python apply_supabase_schema.py <arquivo_sql>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    if not os.path.exists(sql_file):
        print(f"Erro: Arquivo SQL não encontrado: {sql_file}")
        sys.exit(1)
    
    # Carregar e executar SQL
    print(f"Carregando SQL de {sql_file}...")
    sql_content = load_sql_file(sql_file)
    
    print("Conectando ao Supabase...")
    success = execute_sql_statements(sql_content)
    
    if success:
        print("\nEsquema aplicado com sucesso!")
    else:
        print("\nHouve erros ao aplicar o esquema. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()