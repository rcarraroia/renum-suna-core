"""
Script de teste para validar correções de WebSocket
Testa especificamente os problemas de tokens vazios e falhas de handshake
"""

import asyncio
import json
import logging
import time
import websockets
import requests
from datetime import datetime
from typing import List, Dict, Any

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketFixesValidator:
    """Validador das correções implementadas"""
    
    def __init__(self, base_url: str = "http://localhost:8000", ws_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.test_results = []
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes de validação"""
        logger.info("🧪 Iniciando testes de validação das correções WebSocket")
        
        tests = [
            ("Teste de Token Vazio", self.test_empty_token),
            ("Teste de Token Inválido", self.test_invalid_token),
            ("Teste de Token Válido", self.test_valid_token),
            ("Teste de Fallback de Autenticação", self.test_auth_fallback),
            ("Teste de Handshake com Retry", self.test_handshake_retry),
            ("Teste de Conexão sem Token", self.test_no_token_connection),
            ("Teste de Múltiplas Conexões", self.test_multiple_connections),
            ("Teste de Reconexão", self.test_reconnection),
            ("Teste de Heartbeat", self.test_heartbeat),
            ("Teste de Broadcast", self.test_broadcast)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🔍 Executando: {test_name}")
                result = await test_func()
                
                if result["success"]:
                    logger.info(f"✅ {test_name}: PASSOU")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name}: FALHOU - {result.get('error', 'Erro desconhecido')}")
                    failed += 1
                
                self.test_results.append({
                    "test": test_name,
                    "success": result["success"],
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"💥 {test_name}: ERRO CRÍTICO - {str(e)}")
                failed += 1
                self.test_results.append({
                    "test": test_name,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Pequena pausa entre testes
            await asyncio.sleep(1)
        
        # Gerar relatório final
        report = {
            "summary": {
                "total_tests": len(tests),
                "passed": passed,
                "failed": failed,
                "success_rate": (passed / len(tests)) * 100 if tests else 0
            },
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Relatório Final: {passed}/{len(tests)} testes passaram ({report['summary']['success_rate']:.1f}%)")
        
        return report
    
    async def test_empty_token(self) -> Dict[str, Any]:
        """Testa comportamento com token vazio"""
        try:
            # Teste 1: Token vazio na URL
            uri = f"{self.ws_url}/ws?token="
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Aguardar mensagem de solicitação de token
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "token_required":
                    return {
                        "success": True,
                        "message": "Sistema solicitou token corretamente para token vazio",
                        "response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Resposta inesperada: {data}"
                    }
                    
        except websockets.exceptions.ConnectionClosedError as e:
            # Conexão fechada é aceitável se for por falta de autenticação
            if e.code == 1008:  # Policy Violation
                return {
                    "success": True,
                    "message": "Conexão fechada corretamente por falta de autenticação",
                    "close_code": e.code
                }
            else:
                return {
                    "success": False,
                    "error": f"Conexão fechada com código inesperado: {e.code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}"
            }
    
    async def test_invalid_token(self) -> Dict[str, Any]:
        """Testa comportamento com token inválido"""
        try:
            invalid_token = "invalid.jwt.token"
            uri = f"{self.ws_url}/ws?token={invalid_token}"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Aguardar resposta
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "error" and "inválido" in data.get("error", "").lower():
                    return {
                        "success": True,
                        "message": "Token inválido rejeitado corretamente",
                        "response": data
                    }
                elif data.get("type") == "token_required":
                    return {
                        "success": True,
                        "message": "Sistema solicitou novo token para token inválido",
                        "response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Resposta inesperada para token inválido: {data}"
                    }
                    
        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 1008:  # Policy Violation
                return {
                    "success": True,
                    "message": "Conexão fechada corretamente por token inválido",
                    "close_code": e.code
                }
            else:
                return {
                    "success": False,
                    "error": f"Código de fechamento inesperado: {e.code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}"
            }
    
    async def test_valid_token(self) -> Dict[str, Any]:
        """Testa comportamento com token válido (simulado)"""
        try:
            # Gerar token de teste (simulado)
            test_token = self._generate_test_token()
            uri = f"{self.ws_url}/ws?token={test_token}"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Aguardar confirmação de conexão
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "connection_established":
                    return {
                        "success": True,
                        "message": "Conexão estabelecida com token válido",
                        "response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Resposta inesperada para token válido: {data}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro com token válido: {str(e)}"
            }
    
    async def test_auth_fallback(self) -> Dict[str, Any]:
        """Testa sistema de fallback de autenticação"""
        try:
            # Conectar sem token
            uri = f"{self.ws_url}/ws"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Aguardar solicitação de token
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "token_required":
                    # Enviar token via WebSocket
                    test_token = self._generate_test_token()
                    await websocket.send(json.dumps({
                        "type": "auth_token",
                        "token": test_token
                    }))
                    
                    # Aguardar confirmação
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "connection_established":
                        return {
                            "success": True,
                            "message": "Fallback de autenticação funcionou",
                            "response": data
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Fallback falhou: {data}"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Sistema não solicitou token: {data}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no fallback: {str(e)}"
            }
    
    async def test_handshake_retry(self) -> Dict[str, Any]:
        """Testa sistema de retry no handshake"""
        try:
            # Tentar múltiplas conexões rapidamente
            success_count = 0
            total_attempts = 5
            
            for i in range(total_attempts):
                try:
                    test_token = self._generate_test_token()
                    uri = f"{self.ws_url}/ws?token={test_token}"
                    
                    async with websockets.connect(uri, timeout=5) as websocket:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3)
                        data = json.loads(response)
                        
                        if data.get("type") == "connection_established":
                            success_count += 1
                            
                except Exception as e:
                    logger.warning(f"Tentativa {i+1} falhou: {str(e)}")
                
                await asyncio.sleep(0.5)
            
            success_rate = (success_count / total_attempts) * 100
            
            return {
                "success": success_rate >= 60,  # Pelo menos 60% de sucesso
                "message": f"Taxa de sucesso no handshake: {success_rate:.1f}%",
                "successful_connections": success_count,
                "total_attempts": total_attempts
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no teste de retry: {str(e)}"
            }
    
    async def test_no_token_connection(self) -> Dict[str, Any]:
        """Testa conexão sem token algum"""
        try:
            uri = f"{self.ws_url}/ws"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                # Deve solicitar token ou permitir modo guest
                if data.get("type") in ["token_required", "connection_established"]:
                    return {
                        "success": True,
                        "message": "Conexão sem token tratada corretamente",
                        "response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Resposta inesperada sem token: {data}"
                    }
                    
        except websockets.exceptions.ConnectionClosedError as e:
            # Aceitável se fechar por falta de autenticação
            return {
                "success": True,
                "message": "Conexão fechada corretamente por falta de token",
                "close_code": e.code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro sem token: {str(e)}"
            }
    
    async def test_multiple_connections(self) -> Dict[str, Any]:
        """Testa múltiplas conexões simultâneas"""
        try:
            connections = []
            max_connections = 10
            
            # Criar múltiplas conexões
            for i in range(max_connections):
                try:
                    test_token = self._generate_test_token(user_id=f"user_{i}")
                    uri = f"{self.ws_url}/ws?token={test_token}"
                    
                    websocket = await websockets.connect(uri, timeout=5)
                    connections.append(websocket)
                    
                    # Aguardar confirmação
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    
                except Exception as e:
                    logger.warning(f"Conexão {i} falhou: {str(e)}")
            
            success_rate = (len(connections) / max_connections) * 100
            
            # Fechar todas as conexões
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
            
            return {
                "success": success_rate >= 70,  # Pelo menos 70% de sucesso
                "message": f"Múltiplas conexões: {len(connections)}/{max_connections} ({success_rate:.1f}%)",
                "successful_connections": len(connections),
                "attempted_connections": max_connections
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro em múltiplas conexões: {str(e)}"
            }
    
    async def test_reconnection(self) -> Dict[str, Any]:
        """Testa capacidade de reconexão"""
        try:
            test_token = self._generate_test_token()
            uri = f"{self.ws_url}/ws?token={test_token}"
            
            # Primeira conexão
            websocket1 = await websockets.connect(uri, timeout=5)
            response1 = await asyncio.wait_for(websocket1.recv(), timeout=3)
            await websocket1.close()
            
            # Aguardar um pouco
            await asyncio.sleep(1)
            
            # Segunda conexão (reconexão)
            websocket2 = await websockets.connect(uri, timeout=5)
            response2 = await asyncio.wait_for(websocket2.recv(), timeout=3)
            await websocket2.close()
            
            data1 = json.loads(response1)
            data2 = json.loads(response2)
            
            if (data1.get("type") == "connection_established" and 
                data2.get("type") == "connection_established"):
                return {
                    "success": True,
                    "message": "Reconexão funcionou corretamente",
                    "first_connection": data1,
                    "second_connection": data2
                }
            else:
                return {
                    "success": False,
                    "error": "Falha na reconexão",
                    "responses": [data1, data2]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na reconexão: {str(e)}"
            }
    
    async def test_heartbeat(self) -> Dict[str, Any]:
        """Testa sistema de heartbeat"""
        try:
            test_token = self._generate_test_token()
            uri = f"{self.ws_url}/ws?token={test_token}"
            
            async with websockets.connect(uri, timeout=10) as websocket:
                # Aguardar confirmação de conexão
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                # Enviar ping
                await websocket.send(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Aguardar pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    return {
                        "success": True,
                        "message": "Heartbeat funcionando",
                        "response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Resposta de ping inesperada: {data}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no heartbeat: {str(e)}"
            }
    
    async def test_broadcast(self) -> Dict[str, Any]:
        """Testa sistema de broadcast"""
        try:
            # Testar via API HTTP
            response = requests.post(f"{self.base_url}/ws/broadcast", 
                                   json={"message": "Teste de broadcast"}, 
                                   timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": "Broadcast funcionando",
                    "response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no broadcast: {str(e)}"
            }
    
    def _generate_test_token(self, user_id: str = "test_user") -> str:
        """Gera token de teste (simulado)"""
        # Em um ambiente real, isso geraria um JWT válido
        # Por enquanto, retorna um token simulado que o sistema pode reconhecer
        import base64
        
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + 3600,  # 1 hora
            "iat": int(time.time()),
            "test": True
        }
        
        # Token simulado (não é um JWT real)
        token_data = base64.b64encode(json.dumps(payload).encode()).decode()
        return f"test.{token_data}.signature"
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Salva relatório em arquivo"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"websocket_fixes_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Relatório salvo em: {filename}")

async def main():
    """Função principal"""
    validator = WebSocketFixesValidator()
    
    print("🚀 Iniciando validação das correções de WebSocket...")
    print("=" * 60)
    
    # Executar todos os testes
    report = await validator.run_all_tests()
    
    # Salvar relatório
    validator.save_report(report)
    
    # Mostrar resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    
    summary = report["summary"]
    print(f"Total de testes: {summary['total_tests']}")
    print(f"Testes aprovados: {summary['passed']}")
    print(f"Testes falharam: {summary['failed']}")
    print(f"Taxa de sucesso: {summary['success_rate']:.1f}%")
    
    if summary['success_rate'] >= 80:
        print("\n✅ RESULTADO: CORREÇÕES VALIDADAS COM SUCESSO!")
        print("Os problemas de tokens vazios e falhas de handshake foram resolvidos.")
    elif summary['success_rate'] >= 60:
        print("\n🟡 RESULTADO: MELHORIAS SIGNIFICATIVAS DETECTADAS")
        print("A maioria dos problemas foi resolvida, mas ainda há pontos para melhorar.")
    else:
        print("\n❌ RESULTADO: PROBLEMAS PERSISTEM")
        print("As correções não foram suficientes. Revisão adicional necessária.")
    
    print("\n📄 Relatório detalhado salvo em arquivo JSON.")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())