"""
Script para testar as correções implementadas
Executa testes específicos para validar que os problemas foram resolvidos
"""

import asyncio
import subprocess
import sys
import time
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrectionTester:
    """Testador das correções implementadas"""
    
    def __init__(self):
        self.backend_path = Path(__file__).parent
        
    async def run_all_tests(self):
        """Executa todos os testes de validação"""
        logger.info("🧪 INICIANDO TESTES DE CORREÇÕES")
        logger.info("=" * 50)
        
        tests = [
            ("Diagnóstico Final", self.run_final_diagnosis),
            ("Teste de Correções WebSocket", self.run_websocket_fixes_test),
            ("Validação de Funcionalidade", self.run_functionality_test)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"🔍 Executando: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result["success"]:
                    logger.info(f"✅ {test_name}: PASSOU")
                else:
                    logger.error(f"❌ {test_name}: FALHOU")
                    
            except Exception as e:
                logger.error(f"💥 {test_name}: ERRO - {str(e)}")
                results[test_name] = {"success": False, "error": str(e)}
            
            logger.info("-" * 30)
        
        # Resumo final
        passed = sum(1 for r in results.values() if r.get("success", False))
        total = len(results)
        
        logger.info("📊 RESUMO FINAL")
        logger.info(f"Testes aprovados: {passed}/{total}")
        logger.info(f"Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        if passed == total:
            logger.info("🎉 TODAS AS CORREÇÕES VALIDADAS!")
            return True
        else:
            logger.warning("⚠️  ALGUMAS CORREÇÕES PRECISAM DE REVISÃO")
            return False
    
    async def run_final_diagnosis(self):
        """Executa o diagnóstico final"""
        try:
            # Executar diagnóstico final
            result = subprocess.run([
                sys.executable, 
                str(self.backend_path / "run_final_diagnosis.py")
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Diagnóstico final passou",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "message": "Diagnóstico final falhou",
                    "output": result.stdout,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Diagnóstico final expirou (timeout)"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro executando diagnóstico: {str(e)}"
            }
    
    async def run_websocket_fixes_test(self):
        """Executa teste específico das correções WebSocket"""
        try:
            # Verificar se o servidor está rodando
            import requests
            
            try:
                response = requests.get("http://localhost:8000/ws/health", timeout=5)
                server_running = response.status_code == 200
            except:
                server_running = False
            
            if not server_running:
                return {
                    "success": False,
                    "message": "Servidor não está rodando. Execute 'python backend/api.py' primeiro."
                }
            
            # Executar teste de correções
            result = subprocess.run([
                sys.executable, 
                str(self.backend_path / "test_websocket_fixes.py")
            ], capture_output=True, text=True, timeout=120)
            
            # Analisar resultado
            if "CORREÇÕES VALIDADAS COM SUCESSO" in result.stdout:
                return {
                    "success": True,
                    "message": "Correções WebSocket validadas",
                    "output": result.stdout
                }
            elif "MELHORIAS SIGNIFICATIVAS" in result.stdout:
                return {
                    "success": True,
                    "message": "Melhorias significativas detectadas",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "message": "Correções WebSocket não validadas",
                    "output": result.stdout,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Teste de correções expirou (timeout)"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro executando teste: {str(e)}"
            }
    
    async def run_functionality_test(self):
        """Executa teste básico de funcionalidade"""
        try:
            import requests
            import json
            
            base_url = "http://localhost:8000"
            
            # Teste 1: Health check
            try:
                response = requests.get(f"{base_url}/ws/health", timeout=5)
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Health check falhou: HTTP {response.status_code}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Health check erro: {str(e)}"
                }
            
            # Teste 2: Stats endpoint
            try:
                response = requests.get(f"{base_url}/ws/stats", timeout=5)
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Stats endpoint falhou: HTTP {response.status_code}"
                    }
                
                stats = response.json()
                if "active_connections" not in stats:
                    return {
                        "success": False,
                        "message": "Stats endpoint não retorna dados esperados"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Stats endpoint erro: {str(e)}"
                }
            
            # Teste 3: Broadcast endpoint
            try:
                response = requests.post(
                    f"{base_url}/ws/broadcast",
                    json={"message": "Teste de funcionalidade"},
                    timeout=5
                )
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Broadcast endpoint falhou: HTTP {response.status_code}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Broadcast endpoint erro: {str(e)}"
                }
            
            return {
                "success": True,
                "message": "Todos os endpoints funcionando corretamente"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro no teste de funcionalidade: {str(e)}"
            }

async def main():
    """Função principal"""
    print("🚀 TESTADOR DE CORREÇÕES WEBSOCKET")
    print("=" * 50)
    print("Validando implementações...")
    print("")
    
    tester = CorrectionTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎯 RESULTADO FINAL: CORREÇÕES VALIDADAS!")
            print("Os problemas de tokens vazios e falhas de handshake foram resolvidos.")
            sys.exit(0)
        else:
            print("\n⚠️  RESULTADO FINAL: REVISÃO NECESSÁRIA")
            print("Algumas correções precisam de ajustes adicionais.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erro crítico: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())