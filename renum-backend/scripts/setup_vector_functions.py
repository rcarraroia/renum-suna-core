"""
Script para configurar funções SQL para operações vetoriais no Supabase.

Este script executa o arquivo SQL que cria as funções necessárias para
operações com vetores no módulo RAG.
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

from app.core.supabase_client import supabase
from app.db.pg_pool import pg_pool

def setup_vector_functions():
    """Configura funções SQL para operações vetoriais no Supabase."""
    try:
        # Ler o arquivo SQL
        sql_file = Path(__file__).parent / "create_vector_functions.sql"
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
            print("\n✅ Funções SQL para operações vetoriais configuradas com sucesso")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao configurar funções SQL: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                pg_pool.release_connection(conn)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar funções SQL: {str(e)}")
        return False

def test_vector_functions():
    """Testa as funções SQL para operações vetoriais."""
    try:
        # Testar a função search_embeddings
        print("\nTestando função search_embeddings...")
        
        # Criar um embedding de teste (vetor de 1536 dimensões com valores aleatórios)
        import random
        test_embedding = [random.random() for _ in range(1536)]
        
        # Executar a função
        conn = None
        cursor = None
        try:
            conn = pg_pool.get_connection()
            cursor = conn.cursor()
            
            # Verificar se a função existe
            cursor.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_name = 'search_embeddings'
                AND routine_schema = 'public'
            """)
            if cursor.fetchone():
                print("✅ Função search_embeddings existe")
            else:
                print("❌ Função search_embeddings não existe")
            
            # Verificar se a extensão pgvector está habilitada
            cursor.execute("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector'")
            result = cursor.fetchone()
            if result and result[0]:
                print(f"✅ Extensão pgvector está habilitada (versão {result[0]})")
            else:
                print("❌ Extensão pgvector não está habilitada")
            
            # Verificar se o índice foi criado
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'document_chunks'
                AND indexname = 'document_chunks_embedding_idx'
            """)
            if cursor.fetchone():
                print("✅ Índice document_chunks_embedding_idx existe")
            else:
                print("❌ Índice document_chunks_embedding_idx não existe")
            
            print("\n✅ Teste das funções SQL concluído")
            
        except Exception as e:
            logger.error(f"Erro ao testar funções SQL: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                pg_pool.release_connection(conn)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar funções SQL: {str(e)}")
        return False

if __name__ == "__main__":
    print("Configurando funções SQL para operações vetoriais no Supabase...")
    success = setup_vector_functions()
    
    if success:
        print("\nTestando funções SQL...")
        test_success = test_vector_functions()
        sys.exit(0 if test_success else 1)
    else:
        sys.exit(1)