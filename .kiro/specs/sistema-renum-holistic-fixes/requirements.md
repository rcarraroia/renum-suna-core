# Requirements Document

## Introduction

Este documento define os requisitos para uma correção holística e abrangente do sistema Suna-Core e Renum, baseado na auditoria técnica completa realizada. O objetivo é estabilizar, padronizar e preparar todo o sistema para operação contínua em ambiente de produção, resolvendo problemas estruturais, de dependências, infraestrutura, segurança e observabilidade de forma integrada.

## Requirements

### Requirement 1

**User Story:** Como desenvolvedor do sistema, eu quero que todas as dependências estejam padronizadas e atualizadas, para que não haja conflitos de versão e problemas de compatibilidade.

#### Acceptance Criteria

1. WHEN o sistema utiliza Redis THEN SHALL usar exclusivamente `redis.asyncio` em vez de `aioredis` deprecated
2. WHEN as dependências são definidas THEN SHALL ter versões específicas padronizadas em `pyproject.toml`
3. WHEN FastAPI é utilizado THEN SHALL usar versão 0.115.12 ou superior
4. WHEN Supabase é utilizado THEN SHALL usar versão 2.17.0 ou superior
5. WHEN PyJWT é utilizado THEN SHALL usar versão 2.10.1 ou superior

### Requirement 2

**User Story:** Como administrador de sistema, eu quero que a infraestrutura esteja otimizada para produção, para que o sistema tenha performance adequada e estabilidade.

#### Acceptance Criteria

1. WHEN Redis é configurado THEN SHALL ter configuração otimizada com maxmemory, política LRU e persistência
2. WHEN o backend é executado THEN SHALL usar múltiplos workers (4) com UvicornWorker
3. WHEN containers são executados THEN SHALL ter limites de recursos definidos (CPU: 2.0, Memory: 4G)
4. WHEN serviços são iniciados THEN SHALL ter configuração de timeout e logging adequados

### Requirement 3

**User Story:** Como desenvolvedor, eu quero que o banco de dados tenha nomenclatura padronizada e segurança adequada, para que seja fácil de manter e seguro.

#### Acceptance Criteria

1. WHEN tabelas são criadas THEN SHALL ter prefixo `renum_` padronizado
2. WHEN dados são acessados THEN SHALL ter Row Level Security (RLS) ativo em todas as tabelas
3. WHEN controle de acesso é necessário THEN SHALL usar funções do basejump corretamente
4. WHEN migrações são executadas THEN SHALL renomear tabelas existentes para o padrão

### Requirement 4

**User Story:** Como administrador de sistema, eu quero observabilidade completa do sistema, para que possa monitorar performance e identificar problemas rapidamente.

#### Acceptance Criteria

1. WHEN métricas são coletadas THEN SHALL usar Prometheus com instrumentação em FastAPI
2. WHEN dashboards são necessários THEN SHALL ter Grafana configurado com métricas relevantes
3. WHEN erros ocorrem THEN SHALL ter Sentry ativo para logging e rastreamento
4. WHEN endpoints são acessados THEN SHALL expor métricas em `/metrics`

### Requirement 5

**User Story:** Como desenvolvedor frontend, eu quero que as dependências do frontend estejam sincronizadas e otimizadas, para que não haja inconsistências entre admin e frontend.

#### Acceptance Criteria

1. WHEN dependências são instaladas THEN SHALL ter versões alinhadas entre renum-frontend e renum-admin
2. WHEN build é executado THEN SHALL ter code splitting e lazy loading implementados
3. WHEN imagens são utilizadas THEN SHALL ter compressão otimizada
4. WHEN Next.js é usado THEN SHALL ter versão consistente em ambos projetos

### Requirement 6

**User Story:** Como desenvolvedor, eu quero cobertura de testes automatizados adequada, para que o sistema seja confiável e mudanças sejam seguras.

#### Acceptance Criteria

1. WHEN testes de backend são executados THEN SHALL ter cobertura mínima de 80% nos endpoints REST principais
2. WHEN testes de frontend são executados THEN SHALL usar Jest + React Testing Library
3. WHEN páginas críticas são testadas THEN SHALL ter testes automatizados implementados
4. WHEN pytest é executado THEN SHALL validar funcionalidades principais do backend

### Requirement 7

**User Story:** Como membro da equipe, eu quero documentação técnica completa e atualizada, para que seja fácil entender e manter o sistema.

#### Acceptance Criteria

1. WHEN documentação é acessada THEN SHALL usar MkDocs com estrutura organizada
2. WHEN documentação é criada THEN SHALL ter seções para backend, frontend e infraestrutura
3. WHEN documentação é publicada THEN SHALL estar disponível via GitHub Pages ou pipeline integrado
4. WHEN desenvolvedores precisam de referência THEN SHALL ter documentação atualizada e completa

### Requirement 8

**User Story:** Como DevOps, eu quero pipeline CI/CD automatizado e confiável, para que deploys sejam seguros e consistentes.

#### Acceptance Criteria

1. WHEN código é commitado THEN SHALL executar testes automatizados
2. WHEN build é executado THEN SHALL validar lint e compilação
3. WHEN deploy é necessário THEN SHALL ter ambiente staging para validação
4. WHEN produção é atualizada THEN SHALL ter deploy manual controlado
5. WHEN pipeline falha THEN SHALL notificar equipe adequadamente