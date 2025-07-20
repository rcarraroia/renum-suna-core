"""
Servidor MCP simples para Supabase.

Este script implementa um servidor MCP básico para interagir com o Supabase.
"""

import os
import sys
import json
import asyncio
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Métodos MCP
async def list_tables():
    """Listar todas as tabelas do banco de dados."""
    try:
        # Usar a função list_tables que foi criada no SQL Editor
        result = await supabase.rpc("list_tables").execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}

async def execute_query(query):
    """Executar uma consulta SQL."""
    try:
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}

async def list_columns(table_name):
    """Listar colunas de uma tabela."""
    try:
        query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}

async def describe_table(table_name):
    """Obter descrição detalhada de uma tabela."""
    try:
        query = f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM 
            information_schema.columns 
        WHERE 
            table_name = '{table_name}'
        ORDER BY 
            ordinal_position
        """
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}

async def count_rows(table_name):
    """Contar o número de linhas em uma tabela."""
    try:
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        return result.data
    except Exception as e:
        return {"error": str(e)}

# Mapeamento de métodos
methods = {
    "listTables": list_tables,
    "executeQuery": execute_query,
    "listColumns": list_columns,
    "describeTable": describe_table,
    "countRows": count_rows
}

# Protocolo MCP
async def handle_request(request):
    """Manipular uma requisição MCP."""
    try:
        method = request.get("method")
        params = request.get("params", {})
        
        if method not in methods:
            return {"error": f"Method {method} not found"}
        
        if method == "executeQuery":
            result = await methods[method](params.get("query", ""))
        elif method == "listColumns" or method == "describeTable" or method == "countRows":
            result = await methods[method](params.get("table_name", ""))
        else:
            result = await methods[method]()
        
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

async def main():
    """Função principal do servidor MCP."""
    # Listar métodos disponíveis
    tools = [
        {
            "name": "listTables",
            "description": "List all tables in the database",
            "parameters": {}
        },
        {
            "name": "executeQuery",
            "description": "Execute a SQL query",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            }
        },
        {
            "name": "listColumns",
            "description": "List columns of a table",
            "parameters": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                }
            }
        },
        {
            "name": "describeTable",
            "description": "Get detailed description of a table",
            "parameters": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                }
            }
        },
        {
            "name": "countRows",
            "description": "Count the number of rows in a table",
            "parameters": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                }
            }
        }
    ]
    
    # Enviar lista de ferramentas para o Kiro
    print(json.dumps({"jsonrpc": "2.0", "result": {"tools": tools}, "id": "init"}))
    sys.stdout.flush()
    
    # Loop principal para processar requisições
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_id = request.get("id")
            
            if "method" in request:
                if request["method"] == "execute":
                    params = request.get("params", {})
                    tool_call = params.get("tool_call", {})
                    
                    response = await handle_request(tool_call)
                    print(json.dumps({"jsonrpc": "2.0", "result": response, "id": request_id}))
                elif request["method"] == "initialize":
                    # Responder ao método initialize
                    print(json.dumps({
                        "jsonrpc": "2.0", 
                        "result": {
                            "tools": tools,
                            "protocolVersion": "2024-11-05",
                            "serverInfo": {
                                "name": "Supabase MCP Server",
                                "version": "1.0.0"
                            },
                            "capabilities": {}
                        }, 
                        "id": request_id
                    }))
                else:
                    print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}))
            else:
                print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid request"}, "id": request_id}))
            
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())