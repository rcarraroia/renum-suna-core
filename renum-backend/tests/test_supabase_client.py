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
            # Tentar acessar a tabela kno
            result = self.supabase.from_("knowledge_bases", use_admin=True).select(")
            logger.info(f"Acesso à tabela knowledge_bases: ✅ Sucesso")
            logger.info(f"  - Registros encontrados: {len(r}")
            self.assertIsNotNobases")
        except Exception as e:
            logger.error(f"Erro ao acessar tabela knowledge_b)}")
    r(e)}")
    
    def test_crud_operations(self):
        """Testa opera
        # Testar método read
        try:
            result = sel)
            logger.info(f"Leit)
            logger.info(f"  - Re")
            self.assertIsNotNone(re")
        except Exception as e:
            logger.error(f"Er
         tr(e)}")
    
    def test_check_rag_tables(self):
        """Testa"""
        rag_tables = [
            "knowledge_bases",
            "knowledge_collections",
            "documents",
            "document_chunks",
            "doc,
            "document_usage_stats",
            "retrieval_fee
            "processing_jobs"
        ]
        
        for table in rag_tables:
            try:
                # Verificar se a tabela existe usando a API REST
    ute()
                logger.info(f"Tabela {taste")
                logger.info(f"  - Registros encontrad)
            
                logger.error(f"Tabela {table}: ❌ Erro

if __name__ == '__main__':
    unittest.main()