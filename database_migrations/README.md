# Database Migrations - Sistema Renum

Este diretório contém scripts de migração de banco de dados para padronização e segurança do sistema Renum.

## 📋 Visão Geral

As migrações implementam:
1. **Padronização de nomenclatura** - Prefixo `renum_` em todas as tabelas
2. **Segurança RLS** - Row Level Security em todas as tabelas
3. **Validação automática** - Scripts de verificação pós-migração
4. **Rollback seguro** - Scripts de reversão para cada migração

## 📁 Estrutura de Arquivos

```
database_migrations/
├── README.md                                    # Esta documentação
├── run_migrations_safely.py                    # Script principal de execução
├── 001_rename_tables_to_renum_prefix.sql       # Migração 001: Renomear tabelas
├── 001_rename_tables_to_renum_prefix_rollback.sql # Rollback da migração 001
├── 002_implement_rls_policies.sql              # Migração 002: Implementar RLS
├── validate_migration_001.py                   # Validação da migração 001
└── validate_rls_policies.py                    # Validação da migração 002
```

## 🚀 Como Usar

### Pré-requisitos

1. **Backup do banco de dados**:
   ```bash
   # Criar backup completo antes de executar migrações
   pg_dump -h hostname -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Ambiente de teste**:
   - Sempre teste as migrações em ambiente de staging primeiro
   - Valide que a aplicação funciona após as migrações

3. **Dependências Python**:
   ```bash
   # Instalar dependências necessárias
   pip install asyncio asyncpg
   ```

### Execução das Migrações

#### 1. Executar Todas as Migrações

```bash
# Executar todas as migrações em ordem
python database_migrations/run_migrations_safely.py

# Forçar re-execução (mesmo se já aplicadas)
python database_migrations/run_migrations_safely.py --force
```

#### 2. Executar Migração Específica

```bash
# Executar apenas a migração 001
python database_migrations/run_migrations_safely.py --migration 001

# Executar apenas a migração 002
python database_migrations/run_migrations_safely.py --migration 002
```

#### 3. Validação Apenas

```bash
# Validar todas as migrações sem executar
python database_migrations/run_migrations_safely.py --validate-only

# Validar migração específica
python database_migrations/run_migrations_safely.py --migration 001 --validate-only
```

#### 4. Dry Run (Simulação)

```bash
# Ver o que seria executado sem fazer mudanças
python database_migrations/run_migrations_safely.py --dry-run
```

### Validação Manual

#### Validar Migração 001 (Renomeação de Tabelas)

```bash
python database_migrations/validate_migration_001.py
```

#### Validar Migração 002 (Políticas RLS)

```bash
python database_migrations/validate_rls_policies.py
```

## 📊 Detalhes das Migrações

### Migração 001: Padronização de Nomenclatura

**Objetivo**: Renomear tabelas para usar o prefixo `renum_`

**Tabelas Afetadas**:
- `knowledge_bases` → `renum_knowledge_bases`
- `knowledge_collections` → `renum_knowledge_collections`
- `documents` → `renum_documents`
- `document_chunks` → `renum_document_chunks`
- `document_versions` → `renum_document_versions`
- `document_usage_stats` → `renum_document_usage_stats`
- `processing_jobs` → `renum_processing_jobs`

**Características**:
- ✅ Preserva dados existentes
- ✅ Atualiza foreign keys automaticamente
- ✅ Mantém índices e constraints
- ✅ Preserva políticas RLS existentes
- ✅ Rollback disponível

### Migração 002: Row Level Security

**Objetivo**: Implementar políticas RLS abrangentes

**Funcionalidades**:
- ✅ RLS habilitado em todas as tabelas `renum_`
- ✅ Políticas de acesso baseadas em usuário
- ✅ Políticas administrativas para superadmins
- ✅ Funções auxiliares para controle de acesso
- ✅ Auditoria de mudanças de políticas

**Políticas Implementadas**:
- **Usuários**: Acesso apenas aos próprios dados
- **Admins**: Acesso a dados de todos os usuários
- **Superadmins**: Acesso total incluindo configurações do sistema

## 🔒 Segurança

### Princípios de Segurança Implementados

1. **Isolamento de Dados**: Usuários só acessam seus próprios dados
2. **Controle Administrativo**: Admins têm acesso elevado controlado
3. **Auditoria**: Todas as mudanças são registradas
4. **Validação**: Verificação automática pós-migração

### Funções de Segurança Criadas

```sql
-- Verificar se usuário é admin
renum_is_admin(user_id UUID DEFAULT auth.uid()) RETURNS BOOLEAN

-- Verificar se usuário é superadmin
renum_is_superadmin(user_id UUID DEFAULT auth.uid()) RETURNS BOOLEAN

-- Obter client_id do usuário
renum_get_user_client_id(user_id UUID DEFAULT auth.uid()) RETURNS UUID

-- Verificar acesso a equipe
renum_user_can_access_team(team_id UUID, user_id UUID DEFAULT auth.uid()) RETURNS BOOLEAN
```

## 🔄 Rollback (Reversão)

### Quando Fazer Rollback

- Falha na validação pós-migração
- Problemas de performance inesperados
- Incompatibilidade com aplicação
- Erro durante a migração

### Como Fazer Rollback

#### Rollback da Migração 001

```bash
# Conectar ao banco e executar
psql -h hostname -U username -d database_name -f database_migrations/001_rename_tables_to_renum_prefix_rollback.sql
```

#### Rollback Manual

```sql
-- Exemplo: reverter renomeação de tabela
ALTER TABLE renum_knowledge_bases RENAME TO knowledge_bases;
```

## 📝 Logs e Monitoramento

### Log de Migração

Cada execução gera:
- **Log detalhado**: `migration_log_YYYYMMDD_HHMMSS.json`
- **Registro no banco**: Tabela `renum_migration_log`
- **Output no console**: Status em tempo real

### Monitoramento Pós-Migração

```sql
-- Verificar status das migrações
SELECT * FROM renum_migration_log ORDER BY applied_at DESC;

-- Verificar tabelas com RLS
SELECT table_name, row_security 
FROM information_schema.tables 
WHERE table_name LIKE 'renum_%' AND table_schema = 'public';

-- Verificar políticas RLS
SELECT tablename, policyname, cmd 
FROM pg_policies 
WHERE tablename LIKE 'renum_%';
```

## ⚠️ Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco

```bash
# Verificar configuração
python -c "from renum-backend.app.core.config import get_settings; print(get_settings().DATABASE_URL)"

# Testar conexão
python -c "from renum-backend.app.db.database import get_db_instance; import asyncio; asyncio.run(get_db_instance())"
```

#### 2. Migração Já Aplicada

```bash
# Forçar re-execução
python database_migrations/run_migrations_safely.py --force
```

#### 3. Falha na Validação

```bash
# Executar validação específica
python database_migrations/validate_migration_001.py
python database_migrations/validate_rls_policies.py
```

#### 4. Problemas de Permissão

```sql
-- Verificar permissões do usuário
SELECT current_user, session_user;

-- Verificar se pode criar tabelas
CREATE TABLE test_permissions (id INTEGER);
DROP TABLE test_permissions;
```

### Recovery de Emergência

#### 1. Restaurar do Backup

```bash
# Restaurar backup completo
psql -h hostname -U username -d database_name < backup_file.sql
```

#### 2. Rollback Parcial

```sql
-- Desabilitar RLS temporariamente
ALTER TABLE renum_table_name DISABLE ROW LEVEL SECURITY;

-- Remover políticas problemáticas
DROP POLICY policy_name ON renum_table_name;
```

## 📞 Suporte

### Informações para Suporte

Ao reportar problemas, inclua:

1. **Log da migração**: Arquivo JSON gerado
2. **Versão do banco**: `SELECT version();`
3. **Status das migrações**: `SELECT * FROM renum_migration_log;`
4. **Erro específico**: Mensagem completa do erro
5. **Ambiente**: Staging/Production

### Comandos de Diagnóstico

```bash
# Gerar relatório completo
python database_migrations/validate_migration_001.py > migration_001_report.txt
python database_migrations/validate_rls_policies.py > rls_policies_report.txt

# Verificar estrutura do banco
psql -h hostname -U username -d database_name -c "\dt renum_*"
```

## 🎯 Próximos Passos

Após executar as migrações com sucesso:

1. **Atualizar código da aplicação** para usar novos nomes de tabela
2. **Testar funcionalidades críticas** da aplicação
3. **Monitorar performance** do banco de dados
4. **Validar políticas RLS** com diferentes tipos de usuário
5. **Documentar mudanças** para a equipe de desenvolvimento

---

**⚠️ IMPORTANTE**: Sempre execute as migrações em ambiente de teste primeiro e mantenha backups atualizados!