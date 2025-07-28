# Migration Utils - Sistema Renum Holistic Fixes

Este pacote contém utilitários seguros para migração e correção holística do sistema Suna-Core e Renum.

## Visão Geral

Os utilitários de migração foram criados para resolver de forma segura e controlada todos os problemas identificados na auditoria técnica do sistema, incluindo:

- Padronização de dependências (migração de aioredis para redis.asyncio)
- Otimização de configurações de infraestrutura
- Implementação de backups e rollbacks automáticos
- Validação de integridade do sistema

## Componentes

### 1. BackupManager
Gerencia backups automáticos de arquivos críticos antes das migrações.

**Funcionalidades:**
- Backup de arquivos individuais ou diretórios
- Metadados de backup com timestamps
- Sessões de backup organizadas
- Restauração automática de backups

### 2. MigrationValidator
Valida a integridade do sistema antes e depois das migrações.

**Funcionalidades:**
- Validação de dependências Python
- Verificação de configurações Redis
- Validação de Docker Compose
- Teste de conectividade de serviços
- Relatórios de validação detalhados

### 3. RollbackManager
Gerencia rollbacks seguros em caso de problemas durante a migração.

**Funcionalidades:**
- Criação de planos de rollback
- Execução automática de rollbacks
- Rollback de emergência
- Log de operações de rollback

### 4. DependencyMigrator
Migra dependências deprecated de forma segura.

**Funcionalidades:**
- Detecção automática de pacotes deprecated
- Atualização de arquivos requirements
- Migração de imports no código
- Validação pós-migração

### 5. ConfigManager
Gerencia configurações de sistema.

**Funcionalidades:**
- Configuração otimizada do Redis
- Limites de recursos no Docker Compose
- Gerenciamento de variáveis de ambiente
- Validação de configurações

## Uso

### Execução Completa da Migração

```bash
# Executar migração completa
python -m migration_utils.main

# Rollback de emergência
python -m migration_utils.main --rollback
```

### Uso Individual dos Componentes

```python
from migration_utils import BackupManager, MigrationValidator

# Criar backup
backup_manager = BackupManager()
session = backup_manager.create_backup_session("my_migration")
backup_manager.backup_file("config.yaml", session)

# Validar sistema
validator = MigrationValidator()
results = validator.run_comprehensive_validation()
print(validator.generate_validation_report())
```

### Testes

```bash
# Executar testes dos utilitários
python -m migration_utils.test_migration_utils
```

## Fluxo de Migração

1. **Pré-validação**: Verifica estado atual do sistema
2. **Backup**: Cria backup completo de arquivos críticos
3. **Migração de Dependências**: Atualiza pacotes deprecated
4. **Configuração**: Aplica configurações otimizadas
5. **Plano de Rollback**: Cria plano para reverter mudanças
6. **Pós-validação**: Verifica integridade após migração

## Arquivos Críticos Gerenciados

- `docker-compose.yaml` - Configuração de containers
- `backend/pyproject.toml` - Dependências do backend principal
- `renum-backend/requirements.txt` - Dependências do renum-backend
- `backend/services/docker/redis.conf` - Configuração do Redis
- `backend/.env` - Variáveis de ambiente do backend
- `frontend/.env.local` - Variáveis de ambiente do frontend

## Segurança

- **Backups Automáticos**: Todos os arquivos são salvos antes de modificações
- **Validação Contínua**: Sistema é validado em cada etapa
- **Rollback Automático**: Reversão rápida em caso de problemas
- **Logs Detalhados**: Registro completo de todas as operações

## Estrutura de Arquivos

```
migration_utils/
├── __init__.py              # Módulo principal
├── backup_manager.py        # Gerenciamento de backups
├── migration_validator.py   # Validação do sistema
├── rollback_manager.py      # Gerenciamento de rollbacks
├── dependency_migrator.py   # Migração de dependências
├── config_manager.py        # Gerenciamento de configurações
├── main.py                  # Script principal de migração
├── test_migration_utils.py  # Testes dos utilitários
└── README.md               # Esta documentação
```

## Logs e Monitoramento

- **migration.log**: Log detalhado de todas as operações
- **backups/**: Diretório com todos os backups criados
- **rollback_plans/**: Planos de rollback para recuperação

## Exemplo de Uso Completo

```python
import asyncio
from migration_utils.main import SystemMigrationOrchestrator

async def main():
    orchestrator = SystemMigrationOrchestrator()
    
    # Executar migração completa
    success = await orchestrator.run_complete_migration()
    
    if not success:
        # Rollback em caso de falha
        orchestrator.emergency_rollback()

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Problemas Comuns

1. **Falha na validação de dependências**
   - Verificar se Python e pip estão funcionando
   - Executar `pip check` manualmente

2. **Erro de conectividade Redis**
   - Verificar se Redis está rodando
   - Validar configurações de rede

3. **Falha no backup**
   - Verificar permissões de arquivo
   - Garantir espaço em disco suficiente

### Recuperação de Emergência

```bash
# Listar sessões de backup disponíveis
ls backups/

# Rollback manual usando sessão específica
python -c "
from migration_utils import RollbackManager
rm = RollbackManager()
rm.create_emergency_rollback('comprehensive_migration')
"
```

## Contribuição

Para adicionar novos utilitários ou melhorar os existentes:

1. Seguir o padrão de classes existentes
2. Adicionar testes correspondentes
3. Atualizar documentação
4. Garantir compatibilidade com rollback

## Versão

Versão atual: 1.0.0

Compatível com:
- Python 3.11+
- FastAPI 0.115.12+
- Redis 5.0.0+
- Docker Compose 2.0+