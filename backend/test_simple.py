import asyncio
import os

# Configurar JWT_SECRET para teste
os.environ['JWT_SECRET'] = 'test_secret_key_for_validation_testing_purposes_only'

from services.improved_token_validator import ImprovedTokenValidator

async def test_validator():
    print("🧪 Testando ImprovedTokenValidator...")
    
    validator = ImprovedTokenValidator()
    
    # Teste 1: Token vazio
    print("Teste 1: Token vazio")
    result = await validator.validate_token_async('')
    print(f"  Resultado: {result.valid} - {result.error_message}")
    
    # Teste 2: Token inválido
    print("Teste 2: Token inválido")
    result2 = await validator.validate_token_async('invalid.token.here')
    print(f"  Resultado: {result2.valid} - {result2.error_message}")
    
    # Teste 3: Token None
    print("Teste 3: Token None")
    result3 = await validator.validate_token_async(None)
    print(f"  Resultado: {result3.valid} - {result3.error_message}")
    
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    asyncio.run(test_validator())