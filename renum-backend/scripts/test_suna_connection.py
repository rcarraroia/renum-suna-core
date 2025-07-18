#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a conexão com a Suna Core.

Este script testa a conexão com a Suna Core, verificando se a API está disponível
e se é possível executar um agente simples.
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.suna_client import suna_client
from app.core.config import settings

async def test_health_check():
    """Testa o health check da Suna Core."""
    print("Testando health check da Suna Core...")
    
    try:
        is_healthy = await suna_client.health_check()
        
        if is_healthy:
            print("✅ Suna Core está disponível")
        else:
            print("❌ Suna Core não está disponível")
    except Exception as e:
        print(f"❌ Erro ao verificar saúde da Suna Core: {str(e)}")

async def test_available_models():
    """Testa a obtenção de modelos disponíveis."""
    print("\nTestando obtenção de modelos disponíveis...")
    
    try:
        models = await suna_client.get_available_models()
        
        if models:
            print(f"✅ {len(models)} modelos disponíveis:")
            for model in models:
                print(f"  - {model.get('name', 'N/A')}")
        else:
            print("❌ Nenhum modelo disponível")
    except Exception as e:
        print(f"❌ Erro ao obter modelos disponíveis: {str(e)}")

async def test_available_tools():
    """Testa a obtenção de ferramentas disponíveis."""
    print("\nTestando obtenção de ferramentas disponíveis...")
    
    try:
        tools = await suna_client.get_available_tools()
        
        if tools:
            print(f"✅ {len(tools)} ferramentas disponíveis:")
            for tool in tools:
                print(f"  - {tool.get('name', 'N/A')}")
        else:
            print("❌ Nenhuma ferramenta disponível")
    except Exception as e:
        print(f"❌ Erro ao obter ferramentas disponíveis: {str(e)}")

async def test_execute_agent():
    """Testa a execução de um agente simples."""
    print("\nTestando execução de agente simples...")
    
    try:
        # Configuração simples de agente
        agent_config = {
            "model": "gpt-3.5-turbo",
            "tools": []
        }
        
        # Prompt simples
        prompt = "Qual é a capital do Brasil?"
        
        # Executar agente
        print(f"Executando agente com prompt: '{prompt}'")
        result = await suna_client.execute_agent(
            prompt=prompt,
            agent_config=agent_config
        )
        
        if result:
            print("✅ Agente executado com sucesso")
            print(f"Resposta: {result.get('response', 'N/A')}")
        else:
            print("❌ Falha ao executar agente")
    except Exception as e:
        print(f"❌ Erro ao executar agente: {str(e)}")

async def main():
    """Função principal."""
    print(f"Testando conexão com a Suna Core em {settings.SUNA_API_URL}")
    print(f"Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Testar health check
    await test_health_check()
    
    # Testar modelos disponíveis
    await test_available_models()
    
    # Testar ferramentas disponíveis
    await test_available_tools()
    
    # Testar execução de agente
    await test_execute_agent()

if __name__ == "__main__":
    asyncio.run(main())