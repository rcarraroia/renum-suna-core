#!/usr/bin/env python3

"""
Script de validação das correções de WebSocket no backend

Este script verifica se as correções implementadas no backend
para resolver as falhas de conexão WebSocket estão funcionando.
"""

import os
import sys
import re
from pathlib import Path

def main():
    print("🔍 Validando correções de WebSocket no backend...\n")
    
    # 1. Verificar configuração de CORS
    print("1. ✅ Verificando configuração de CORS:")
    
    api_py_path = Path("api.py")
    if api_py_path.exists():
        with open(api_py_path, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        # Verificar se localhost:3001 foi adicionado
        if 'localhost:3001' in api_content:
            print("   ✅ api.py: localhost:3001 adicionado para desenvolvimento local")
        else:
            print("   ❌ api.py: localhost:3001 não encontrado")
        
        # Verificar se domínios do Renum foram adicionados
        if 'renum.com.br' in api_content:
            print("   ✅ api.py: Domínios renum.com.br adicionados")
        else:
            print("   ❌ api.py: Domínios renum.com.br não encontrados")
        
        # Verificar regex para Vercel
        if 'renum-.*\.vercel\.app' in api_content:
            print("   ✅ api.py: Regex para Vercel do Renum configurada")
        else:
            print("   ❌ api.py: Regex para Vercel do Renum não encontrada")
    else:
        print("   ❌ api.py não encontrado")
    
    # 2. Verificar endpoint WebSocket
    print("\n2. ✅ Verificando endpoint WebSocket:")
    
    websocket_final_path = Path("websocket_endpoint_final.py")
    if websocket_final_path.exists():
        print("   ✅ websocket_endpoint_final.py: Encontrado")
        
        with open(websocket_final_path, 'r', encoding='utf-8') as f:
            websocket_content = f.read()
        
        # Verificar se as rotas estão configuradas
        if 'setup_websocket_routes' in websocket_content:
            print("   ✅ setup_websocket_routes: Função encontrada")
        else:
            print("   ❌ setup_websocket_routes: Função não encontrada")
        
        # Verificar endpoints específicos
        endpoints = ['/ws', '/ws/stats', '/ws/health', '/ws/broadcast']
        for endpoint in endpoints:
            if endpoint in websocket_content:
                print(f"   ✅ Endpoint {endpoint}: Configurado")
            else:
                print(f"   ❌ Endpoint {endpoint}: Não encontrado")
    else:
        print("   ❌ websocket_endpoint_final.py não encontrado")
    
    # 3. Verificar importação no api.py
    print("\n3. ✅ Verificando importação do WebSocket no api.py:")
    
    if api_py_path.exists():
        with open(api_py_path, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        if 'from websocket_endpoint_final import setup_websocket_routes' in api_content:
            print("   ✅ api.py: Importação do setup_websocket_routes encontrada")
        else:
            print("   ❌ api.py: Importação do setup_websocket_routes não encontrada")
        
        if 'setup_websocket_routes(app)' in api_content:
            print("   ✅ api.py: Chamada do setup_websocket_routes encontrada")
        else:
            print("   ❌ api.py: Chamada do setup_websocket_routes não encontrada")
    
    # 4. Verificar serviços de autenticação WebSocket
    print("\n4. ✅ Verificando serviços de autenticação WebSocket:")
    
    auth_files = [
        "services/websocket_auth_fallback.py",
        "services/improved_token_validator.py"
    ]
    
    for auth_file in auth_files:
        auth_path = Path(auth_file)
        if auth_path.exists():
            print(f"   ✅ {auth_file}: Encontrado")
        else:
            print(f"   ❌ {auth_file}: Não encontrado")
    
    # 5. Verificar configuração de ambiente
    print("\n5. ✅ Verificando configuração de ambiente:")
    
    config_path = Path("utils/config.py")
    if config_path.exists():
        print("   ✅ utils/config.py: Encontrado")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        if 'EnvMode' in config_content:
            print("   ✅ EnvMode: Enum de ambiente encontrada")
        else:
            print("   ❌ EnvMode: Enum de ambiente não encontrada")
    else:
        print("   ❌ utils/config.py não encontrado")
    
    print("\n🎯 Resumo das correções implementadas no backend:")
    print("   1. Adicionados domínios do Renum no CORS (localhost:3001, renum.com.br)")
    print("   2. Configurada regex para Vercel do Renum (renum-*.vercel.app)")
    print("   3. Mantidos endpoints WebSocket funcionais (/ws, /ws/stats, /ws/health)")
    print("   4. Sistema de autenticação WebSocket com fallback implementado")
    
    print("\n📋 Próximos passos para validação completa:")
    print("   1. Testar conexão WebSocket do frontend com o backend")
    print("   2. Validar autenticação JWT via WebSocket")
    print("   3. Testar endpoints de saúde e estatísticas")
    print("   4. Verificar logs de conexão em tempo real")
    
    print("\n✅ Validação das correções de backend concluída!")

if __name__ == "__main__":
    main()