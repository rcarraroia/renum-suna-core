#!/usr/bin/env python3
"""
Teste de integração para validar as correções de produção do Renum Backend.
"""

import sys
import traceback

def test_imports():
    """Testa se todos os módulos principais podem ser importados."""
    print("🔍 Testando importações...")
    
    try:
        # Teste 1: Configuração e is_feature_enabled
        from app.core.config import get_settings, is_feature_enabled
        settings = get_settings()
        assert is_feature_enabled('rag_module') == True
        assert is_feature_enabled('websocket') == True
        assert is_feature_enabled('unknown_feature') == False
        print("✅ Configuração e is_feature_enabled funcionando")
        
        # Teste 2: Modelos de dados
        from app.models.team_models import PaginatedTeamResponse, UserAPIKeyCreate, ExecutionStatus
        print("✅ Modelos de dados importados com sucesso")
        
        # Teste 3: Dependências
        from app.core.dependencies import get_redis_client
        print("✅ Dependências importadas com sucesso")
        
        # Teste 4: Aplicação FastAPI
        from app.main import app
        print("✅ FastAPI app criado com sucesso")
        
        # Teste 5: Módulo RAG
        from app.rag.api import router as rag_router
        print("✅ Módulo RAG importado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        traceback.print_exc()
        return False

def test_functionality():
    """Testa funcionalidades básicas."""
    print("\n🔍 Testando funcionalidades...")
    
    try:
        # Teste da função is_feature_enabled
        from app.core.config import is_feature_enabled
        
        # Testa funcionalidades habilitadas
        assert is_feature_enabled('rag_module') == True
        assert is_feature_enabled('websocket') == True
        assert is_feature_enabled('notifications') == True
        assert is_feature_enabled('team_orchestration') == True
        
        # Testa funcionalidade desconhecida
        assert is_feature_enabled('unknown_feature') == False
        
        print("✅ Função is_feature_enabled funcionando corretamente")
        
        # Teste de configurações
        from app.core.config import get_settings
        settings = get_settings()
        assert settings.PROJECT_NAME == "Renum Backend"
        assert settings.VERSION == "0.1.0"
        
        print("✅ Configurações carregadas corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na funcionalidade: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Testa se a aplicação FastAPI pode ser criada."""
    print("\n🔍 Testando criação da aplicação...")
    
    try:
        from app.main import app
        
        # Verifica se o app foi criado
        assert app is not None
        assert hasattr(app, 'routes')
        
        # Verifica se há rotas registradas
        routes_count = len(app.routes)
        assert routes_count > 0
        
        print(f"✅ FastAPI app criado com {routes_count} rotas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação do app: {e}")
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes de integração do Renum Backend\n")
    
    tests = [
        ("Importações", test_imports),
        ("Funcionalidades", test_functionality),
        ("Criação do App", test_app_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Executando teste: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSOU")
        else:
            print(f"❌ {test_name}: FALHOU")
    
    print(f"\n📊 Resultado final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! O Renum Backend está pronto para produção.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())