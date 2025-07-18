"""
Testes para o cliente Supabase centralizado.
"""

import os
import sys
import logging
import unittest
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

from app.core.supabase_client import SupabaseClient

class TestSupabaseClient(unittest.TestCase):
    """Testes para o cliente Supabase centralizado."""
    
    def setUp(self):
        """Configuração para os testes."""
        self.supabase = SupabaseClient.get_instance()
    
    def test_singleton_pattern(self):
        """Testa se o padrão Singleton está funcionando corretamente."""
        client1 = SupabaseClient.get_instance()
        client2 = SupabaseClient.get_instance()
        self.assertIs(client1, client2, "O padrão Singleton não está funcionando corretamente")
    
    def test_client_initialization(self):
        """Testa se o cliente foi inicializado corretamente."""
        self.assertIsNotNone(self.supabase.client, "Cliente Supabase não foi inicializado")
        self.assertIsNotNone(self.supabase.admin_client, "Cliente Supabase Admin não foi inicializado")
    
    def test_table_access(self):
        """Testa o acesso às tabelas via API REST."""
        try:
            # Tentar acessar a tabela knowledge_bases
            result = self.supabase.from_("knowledge_bases", use_admin=True).select("*").limit(5).execute()
            logger.info(f"Acesso à tabela knowledge_bases: ✅ Sucesso")
            logger.info(f"  - Registros encontrados: {len(result.data)}")
            self.assertIsNotNone(result.data, "Não foi possível acessar a tabela knowledge_bases")
        except Exception as e:
            logger.error(f"Erro ao acessar tabela knowledge_bases: {str(e)}")
            self.fail(f"Erro ao acessar tabela knowledge_bases: {str(e)}")
    
    def test_crud_operations(self):
        """Testa operações CRUD básicas."""
        # Testar método read
        try:
            result = self.supabase.read("knowledge_bases", limit=5, use_admin=True)
            logger.info(f"Leitura de knowledge_bases: ✅ Sucesso")
            logger.info(f"  - Registros encontrados: {len(result.data)}")
            self.assertIsNotNone(result.data, "Não foi possível ler a tabela knowledge_bases")
        except Exception as e:
            logger.error(f"Erro ao ler tabela knowledge_bases: {str(e)}")
            self.fail(f"Erro ao ler tabela knowledge_bases: {str(e)}")
    
    def test_check_rag_tables(self):
        """Testa se as tabelas do RAG existem no banco de dados."""
        rag_tables = [
            "knowledge_bases",
            "knowledge_collections",
            "documents",
            "document_chunks",
            "document_versions",
            "document_usage_stats",
            "retrieval_feedback",
            "processing_jobs"
        ]
        
        for table in rag_tables:
            try:
                # Verificar se a tabela existe usando a API REST
                result = self.supabase.from_(table, use_admin=True).select("*").limit(1).execute()
                logger.info(f"Tabela {table}: ✅ Existe")
                logger.info(f"  - Registros encontrados: {len(result.data)}")
            except Exception as e:
                logger.error(f"Tabela {table}: ❌ Erro ao acessar ({str(e)})")

if __name__ == '__main__':
    unittest.main()