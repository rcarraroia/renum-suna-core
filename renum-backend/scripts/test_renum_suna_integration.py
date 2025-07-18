#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a integração completa entre Renum e Suna.

Este script testa o fluxo completo de execução de um agente, desde a criação
até a execução e obtenção de resultados.
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.suna_client import suna_client
from app.services.suna_integration import suna_integration_service
from app.services.agent import agent_service
from app.models.agent import AgentStatus
from app.core.config import settings

async def create_test_agent():
    """Cria um agente de teste."""
    print("Criando agente de teste...")
    
    # Gerar IDs únicos
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Configuração do agente
    agent_config = {
        "model": "gpt-3.5-turbo",
        "tools": [
            {
                "name": "tavily_search",
                "description": "Ferramenta para busca na web usando a API Tavily",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Consulta de busca"
                    }
                }
            }
        ]
    }
    
    try:
        # Criar agente
        agent = await agent_service.create_agent(
            name="Agente de Teste",
            client_id=client_id,
            configuration=agent_config,
            description="Agente para teste de integração Renum-Suna",
            created_by=user_id,
            status=AgentStatus.ACTIVE
        )
        
        print(f"✅ Agente criado com sucesso: {agent.id}")
        return agent, user_id
    except Exception as e:
        print(f"❌ Erro ao criar agente: {str(e)}")
        return None, None

async def execute_test_agent(agent, user_id):
    """Executa o agente de teste."""
    print("\nExecutando agente de teste...")
    
    # Prompt de teste
    prompt = "Qual é a capital do Brasil? Forneça algumas informações interessantes sobre ela."
    
    try:
        # Executar agente
        execution = await suna_integration_service.execute_agent(
            agent_id=agent.id,
            user_id=user_id,
            prompt=prompt
        )
        
        print(f"✅ Execução iniciada com sucesso: {execution.id}")
        print(f"Status inicial: {execution.status}")
        
        return execution
    except Exception as e:
        print(f"❌ Erro ao executar agente: {str(e)}")
        return None

async def monitor_execution(execution_id, max_attempts=10, delay=2):
    """Monitora o status de uma execução."""
    print("\nMonitorando execução...")
    
    for attempt in range(max_attempts):
        try:
            # Obter status da execução
            execution = await suna_integration_service.get_execution_status(execution_id)
            
            print(f"Tentativa {attempt + 1}/{max_attempts}: Status = {execution.status}")
            
            # Se a execução foi concluída ou falhou, parar de monitorar
            if execution.status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                print(f"\n✅ Execução finalizada com status: {execution.status}")
                
                if execution.output:
                    print("\nResposta:")
                    print("-" * 40)
                    print(execution.output.get("response", "Sem resposta"))
                    print("-" * 40)
                
                if execution.error:
                    print(f"\nErro: {execution.error}")
                
                if execution.tokens_used:
                    print(f"\nTokens utilizados: {execution.tokens_used}")
                
                return execution
            
            # Aguardar antes da próxima tentativa
            await asyncio.sleep(delay)
        except Exception as e:
            print(f"❌ Erro ao monitorar execução: {str(e)}")
            await asyncio.sleep(delay)
    
    print("❌ Tempo limite excedido ao monitorar execução")
    return None

async def test_cancel_execution(execution_id):
    """Testa o cancelamento de uma execução."""
    print("\nTestando cancelamento de execução...")
    
    try:
        # Cancelar execução
        execution = await suna_integration_service.cancel_execution(execution_id)
        
        print(f"✅ Execução cancelada com sucesso: {execution.status}")
        return execution
    except Exception as e:
        print(f"❌ Erro ao cancelar execução: {str(e)}")
        return None

async def main():
    """Função principal."""
    print(f"Testando integração Renum-Suna")
    print(f"Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Verificar se a Suna Core está disponível
    is_healthy = await suna_client.health_check()
    if not is_healthy:
        print("❌ Suna Core não está disponível. Abortando teste.")
        return
    
    print("✅ Suna Core está disponível")
    
    # Criar agente de teste
    agent, user_id = await create_test_agent()
    if not agent:
        return
    
    # Executar agente
    execution = await execute_test_agent(agent, user_id)
    if not execution:
        return
    
    # Escolher entre monitorar ou cancelar a execução
    choice = input("\nDeseja (M)onitorar ou (C)ancelar a execução? [M/C]: ").strip().upper()
    
    if choice == "C":
        # Cancelar execução
        await test_cancel_execution(execution.id)
    else:
        # Monitorar execução
        await monitor_execution(execution.id)
    
    print("\nTeste de integração Renum-Suna concluído")

if __name__ == "__main__":
    asyncio.run(main())