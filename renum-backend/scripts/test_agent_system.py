"""
Script para testar o sistema de gerenciamento de agentes da Plataforma Renum.
Este script testa a criação, atualização, listagem e exclusão de agentes,
bem como a execução de agentes e o gerenciamento de suas execuções.
"""

import os
import sys
import asyncio
import logging
import json
import uuid
from pathlib import Path
from datetime import datetime

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

from app.models.agent import AgentStatus, AgentExecutionStatus
from app.services.agent import agent_service

async def test_agent_system():
    """Testa o sistema de gerenciamento de agentes."""
    try:
        print("\n=== Testando Sistema de Gerenciamento de Agentes ===\n")
        
        # Gerar IDs de teste
        client_id = uuid.uuid4()
        user_id = uuid.uuid4()
        knowledge_base_id = uuid.uuid4()
        
        print(f"Usando client_id: {client_id}")
        print(f"Usando user_id: {user_id}")
        print(f"Usando knowledge_base_id: {knowledge_base_id}")
        
        # 1. Criar um agente
        print("\n1. Criando um agente de teste...")
        agent_config = {
            "model": "gpt-4",
            "tools": [
                {
                    "name": "search",
                    "description": "Busca informações na internet"
                },
                {
                    "name": "calculator",
                    "description": "Realiza cálculos matemáticos"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        agent = await agent_service.create_agent(
            name="Agente de Teste",
            client_id=client_id,
            configuration=agent_config,
            description="Um agente para testar o sistema",
            knowledge_base_ids=[knowledge_base_id],
            created_by=user_id,
            status=AgentStatus.DRAFT,
            metadata={"test": True, "purpose": "testing"}
        )
        
        print(f"✅ Agente criado com sucesso: {agent.id}")
        print(f"   Nome: {agent.name}")
        print(f"   Status: {agent.status}")
        print(f"   Criado em: {agent.created_at}")
        
        # 2. Recuperar o agente criado
        print("\n2. Recuperando o agente criado...")
        retrieved_agent = await agent_service.get_agent(agent.id)
        
        if retrieved_agent:
            print(f"✅ Agente recuperado com sucesso: {retrieved_agent.id}")
            print(f"   Nome: {retrieved_agent.name}")
            print(f"   Status: {retrieved_agent.status}")
        else:
            print("❌ Falha ao recuperar o agente")
            return False
        
        # 3. Atualizar o agente
        print("\n3. Atualizando o agente...")
        updated_agent = await agent_service.update_agent(
            agent_id=agent.id,
            name="Agente de Teste Atualizado",
            description="Descrição atualizada",
            updated_by=user_id
        )
        
        print(f"✅ Agente atualizado com sucesso: {updated_agent.id}")
        print(f"   Nome: {updated_agent.name}")
        print(f"   Descrição: {updated_agent.description}")
        print(f"   Atualizado em: {updated_agent.updated_at}")
        
        # 4. Atualizar o status do agente
        print("\n4. Atualizando o status do agente para ACTIVE...")
        active_agent = await agent_service.update_agent_status(
            agent_id=agent.id,
            status=AgentStatus.ACTIVE,
            updated_by=user_id
        )
        
        print(f"✅ Status do agente atualizado com sucesso: {active_agent.status}")
        
        # 5. Listar agentes
        print("\n5. Listando agentes do cliente...")
        agents = await agent_service.list_agents(client_id=client_id)
        
        print(f"✅ {len(agents)} agentes encontrados para o cliente {client_id}")
        for a in agents:
            print(f"   - {a.id}: {a.name} ({a.status})")
        
        # 6. Executar o agente
        print("\n6. Executando o agente...")
        execution = await agent_service.execute_agent(
            agent_id=agent.id,
            user_id=user_id,
            input_data={"query": "Qual é a capital do Brasil?"},
            metadata={"source": "test_script"}
        )
        
        print(f"✅ Execução iniciada com sucesso: {execution.id}")
        print(f"   Status: {execution.status}")
        print(f"   Iniciada em: {execution.started_at}")
        
        # 7. Recuperar a execução
        print("\n7. Recuperando a execução...")
        retrieved_execution = await agent_service.get_execution(execution.id)
        
        if retrieved_execution:
            print(f"✅ Execução recuperada com sucesso: {retrieved_execution.id}")
            print(f"   Status: {retrieved_execution.status}")
        else:
            print("❌ Falha ao recuperar a execução")
            return False
        
        # 8. Atualizar o status da execução
        print("\n8. Atualizando o status da execução para COMPLETED...")
        completed_execution = await agent_service.update_execution_status(
            execution_id=execution.id,
            status=AgentExecutionStatus.COMPLETED,
            output={"answer": "Brasília é a capital do Brasil."},
            tokens_used=150
        )
        
        print(f"✅ Status da execução atualizado com sucesso: {completed_execution.status}")
        print(f"   Tokens utilizados: {completed_execution.tokens_used}")
        print(f"   Concluída em: {completed_execution.completed_at}")
        
        # 9. Listar execuções
        print("\n9. Listando execuções do agente...")
        executions = await agent_service.list_executions(agent_id=agent.id)
        
        print(f"✅ {len(executions)} execuções encontradas para o agente {agent.id}")
        for e in executions:
            print(f"   - {e.id}: {e.status} (iniciada em {e.started_at})")
        
        # 10. Excluir o agente
        print("\n10. Excluindo o agente...")
        success = await agent_service.delete_agent(agent.id)
        
        if success:
            print(f"✅ Agente excluído com sucesso: {agent.id}")
        else:
            print(f"❌ Falha ao excluir o agente: {agent.id}")
            return False
        
        print("\n✅ Todos os testes concluídos com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao testar sistema de agentes: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testando sistema de gerenciamento de agentes...")
    asyncio.run(test_agent_system())