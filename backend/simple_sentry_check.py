import os
import sys

print("🔍 Validando Configuração do Sentry")
print("=" * 50)

# Verificar DSN
sentry_dsn = os.getenv("SENTRY_DSN", None)
print(f"DSN Configurado: {'✅' if sentry_dsn else '❌'}")

if sentry_dsn:
    print(f"DSN: {sentry_dsn[:20]}...")

# Verificar imports
try:
    import sentry_sdk
    print("sentry_sdk disponível: ✅")
except ImportError:
    print("sentry_sdk disponível: ❌")

try:
    import sentry
    print("sentry module disponível: ✅")
except ImportError:
    print("sentry module disponível: ❌")

# Verificar arquivo de configuração
import pathlib
config_file = pathlib.Path("sentry.py")
print(f"Arquivo sentry.py existe: {'✅' if config_file.exists() else '❌'}")

if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Configurações encontradas:")
    if "traces_sample_rate" in content:
        print("  - traces_sample_rate: ✅")
    if "send_default_pii" in content:
        print("  - send_default_pii: ✅")
    if "integrations" in content:
        print("  - integrations: ✅")
    if "environment" not in content:
        print("  - environment: ❌ (não configurado)")
    if "release" not in content:
        print("  - release: ❌ (não configurado)")

print("\n💡 Recomendações:")
if not sentry_dsn:
    print("1. Configure SENTRY_DSN environment variable")
print("2. Adicionar environment e release na configuração")
print("3. Adicionar mais integrações (FastAPI, Redis, SQLAlchemy)")
print("4. Implementar filtros before_send")
print("5. Adicionar contexto estruturado")