"""
Script para configurar as tabelas de agentes no Supabase.
Este script executa o arquivo SQL que cria as tabelas necessárias para
gerenciamento de agentes e suas execuções.
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
from dotenv import load_dotenv
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"Carregando variáveis de ambiente de: {env_file}")

from app.db.pg_pool import pg_pool

def setup_agent_tables():
    """Configura as tabelas de agentes no Supabase."""
    try:
        # Ler o arquivo SQL
        sql_file = Path(__file__).parent / "init_agent_tables.sql"
        with open(sql_file, "r") as f:
            sql = f.read()
        
        # Dividir o arquivo em comandos SQL individuais
        # (separados por ponto e vírgula seguido de nova linha ou fim de arquivo)
        sql_commands = sql.split(";\n")
        
        # Executar cada comando SQL
        conn = None
        cursor = None
        try:
            conn = pg_pool.get_connection()
            cursor = conn.cursor()
            for i, command in enumerate(sql_commands):
                command = command.strip()
                if command:  # Ignorar linhas vazias
                    try:
                        print(f"Executando comando SQL {i+1}/{len(sql_commands)}...")
                        cursor.execute(command + ";")
                        print(f"✅ Comando SQL {i+1} executado com sucesso")
                    except Exception as e:
                        print(f"❌ Erro ao executar comando SQL {i+1}: {str(e)}")
            
            # Commit das alterações
            conn.commit()
            print("\n✅ Tabelas de agentes configuradas com sucesso")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao configurar tabelas: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                pg_pool.release_connection(conn)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar tabelas: {str(e)}")
        return False

def test_agent_tables():
    """Testa as tabelas de agentes."""
    try:
        print("\nTestando tabelas de agentes...")
        conn = None
        cursor = None
        try:
            conn = pg_pool.get_connection()
            cursor = conn.cursor()
            
            # Verificar se as tabelas existem
            tables = ["agents", "agent_executions"]
            for table in tables:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    )
                """)
                exists = cursor.fetchone()[0]
                if exists:
                    print(f"✅ Tabela {table} existe")
                else:
                    print(f"❌ Tabela {table} não existe")
            
            print("\n✅ Teste das tabelas concluído")
        except Exception as e:
            logger.error(f"Erro ao testar tabelas: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                pg_pool.release_connection(conn)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar tabelas: {str(e)}")
        return False

if __name__ == "__main__":
    print("Configurando tabelas de agentes no Supabase...")
    success = setup_agent_tables()
    if success:
        print("\nTestando tabelas...")
        test_success = test_agent_tables()
        sys.exit(0 if test_success else 1)
    else:
        sys.exit(1)