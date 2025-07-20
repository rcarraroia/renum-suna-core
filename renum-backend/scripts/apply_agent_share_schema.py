"""
Script para aplicar o esquema de compartilhamento de agentes no Supabase.
Este script usa o cliente Supabase já implementado no projeto.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("apply-schema")

# Adicionar o diretório raiz ao path para importar módulos do projeto
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

try:
    # Importar o cliente Supabase do projeto
    from app.core.supabase_client import supabase
    logger.info("Cliente Supabase importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar cliente Supabase: {e}")
    sys.exit(1)

def load_sql_file(file_path):
    """Carrega um arquivo SQL."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo SQL: {e}")
        sys.exit(1)

def split_sql_statements(sql_content):
    """Divide o conteúdo SQL em comandos individuais."""
    # Esta é uma implementação simplificada e pode não funcionar para todos os casos
    # Ignora comentários e divide por ponto e vírgula
    lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            lines.append(line)
    
    sql_content = ' '.join(lines)
    statements = []
    current_statement = []
    
    for char in sql_content:
        current_statement.append(char)
        if char == ';':
            statements.append(''.join(current_statement))
            current_statement = []
    
    # Adicionar o último statement se não terminar com ponto e vírgula
    if current_statement:
        statements.append(''.join(current_statement))
    
    return [stmt.strip() for stmt in statements if stmt.strip()]

def execute_sql_statements(statements):
    """Executa comandos SQL no Supabase."""
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        if not statement:
            continue
            
        try:
            logger.info(f"Executando comando {i}/{len(statements)}: {statement[:100]}...")
            
            # Executar o comando SQL
            result = supabase.execute_query(statement, use_admin=True)
            
            logger.info(f"Comando {i} executado com sucesso")
            success_count += 1
                
        except Exception as e:
            logger.error(f"Erro ao executar comando {i}: {e}")
            error_count += 1
    
    logger.info(f"\nResumo: {success_count} comandos executados com sucesso, {error_count} erros")
    return error_count == 0

def main():
    """Função principal."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        logger.error("Uso: python apply_agent_share_schema.py <arquivo_sql>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    if not os.path.exists(sql_file):
        logger.error(f"Erro: Arquivo SQL não encontrado: {sql_file}")
        sys.exit(1)
    
    # Carregar SQL
    logger.info(f"Carregando SQL de {sql_file}...")
    sql_content = load_sql_file(sql_file)
    
    # Dividir em comandos
    statements = split_sql_statements(sql_content)
    logger.info(f"Encontrados {len(statements)} comandos SQL")
    
    # Executar comandos
    logger.info("Conectando ao Supabase...")
    success = execute_sql_statements(statements)
    
    if success:
        logger.info("\nEsquema aplicado com sucesso!")
    else:
        logger.error("\nHouve erros ao aplicar o esquema. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()