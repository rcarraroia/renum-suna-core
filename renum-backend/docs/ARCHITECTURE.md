# Arquitetura do Sistema Renum-Suna

Este documento descreve a arquitetura integrada do sistema Renum-Suna, incluindo os componentes, fluxos de dados e considerações de implantação.

## Visão Geral da Arquitetura

O sistema Renum-Suna é composto por quatro componentes principais:

1. **Backend Suna**: Sistema open-source existente que fornece a funcionalidade core de execução de agentes de IA
2. **Backend Renum**: API personalizada que estende o Backend Suna e fornece funcionalidades adicionais
3. **Frontend Renum**: Interface de usuário principal hospedada no Vercel
4. **Painel Admin Renum**: Interface administrativa separada hospedada no Vercel

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│  Frontend Renum │     │ Painel Admin    │
│  (Vercel)       │     │ (Vercel)        │
│                 │     │                 │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│                                         │
│            API Gateway (Nginx)          │
│                                         │
└───────────────┬─────────────┬───────────┘
                │             │
    ┌───────────▼────┐   ┌────▼───────────┐
    │                │   │                │
    │  Backend Renum │   │  Backend Suna  │
    │  (VPS - :9000) │◄──┤  (VPS - :8000) │
    │                │   │                │
    └───────────┬────┘   └────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│                                         │
│         Banco de Dados Supabase         │
│                                         │
└─────────────────────────────────────────┘
```

## Componentes do Sistema

### 1. Backend Suna

- **Função**: Execução de agentes de IA, gerenciamento de conhecimento, integração com LLMs
- **Tecnologia**: Python, FastAPI
- **Localização**: VPS compartilhada
- **Porta**: 8000
- **Considerações**: Sistema open-source que não deve ser modificado para manter compatibilidade com atualizações

### 2. Backend Renum

- **Função**: Extensão do Backend Suna, gerenciamento de usuários, compartilhamento de agentes, métricas
- **Tecnologia**: Python, FastAPI
- **Localização**: Mesma VPS do Backend Suna
- **Porta**: 9000
- **Considerações**: Sistema personalizado que integra com o Backend Suna

### 3. Frontend Renum

- **Função**: Interface de usuário principal para interação com agentes
- **Tecnologia**: Next.js, React
- **Localização**: Vercel
- **Considerações**: Comunica-se com ambos os backends (Renum e Suna)

### 4. Painel Admin Renum

- **Função**: Interface administrativa para configuração, métricas e gerenciamento
- **Tecnologia**: Next.js, React
- **Localização**: Vercel
- **Considerações**: Comunica-se principalmente com o Backend Renum

## Banco de Dados

- **Tecnologia**: PostgreSQL (Supabase)
- **Esquema**: Compartilhado entre Backend Suna e Backend Renum
- **Convenção de Nomenclatura**: Tabelas do Renum usam o prefixo `renum_` para distingui-las das tabelas do Suna

### Tabelas Principais

#### Tabelas do Suna (Existentes)
- `agents`: Configuração de agentes
- `agent_runs`: Execuções de agentes
- `agent_versions`: Versões de agentes
- `knowledge_bases`: Bases de conhecimento
- `documents`: Documentos nas bases de conhecimento
- `document_chunks`: Chunks de documentos com embeddings

#### Tabelas do Renum (Prefixo `renum_`)
- `renum_agent_shares`: Compartilhamento de agentes entre usuários
- `renum_settings`: Configurações específicas da interface Renum
- `renum_metrics`: Métricas e estatísticas coletadas pela interface Renum
- `renum_audit_logs`: Logs de auditoria para ações realizadas na interface Renum

## Fluxos de Dados

### 1. Autenticação de Usuário

```
Frontend Renum → Backend Renum → Supabase Auth → Frontend Renum (token JWT)
```

### 2. Listagem de Agentes

```
Frontend Renum → Backend Renum → Supabase DB → Backend Renum → Frontend Renum
```

### 3. Execução de Agente

```
Frontend Renum → Backend Suna → Execução do Agente → Backend Suna → Frontend Renum
```

### 4. Compartilhamento de Agente

```
Frontend Renum → Backend Renum → Supabase DB (renum_agent_shares) → Backend Renum → Frontend Renum
```

### 5. Métricas e Relatórios

```
Painel Admin → Backend Renum → Supabase DB → Backend Renum → Painel Admin
```

## Segurança e Isolamento de Dados

### Row Level Security (RLS)

O Supabase utiliza políticas RLS para garantir o isolamento de dados entre clientes:

- Cada tabela tem políticas específicas que controlam quais registros um usuário pode ver, criar, atualizar ou excluir
- As políticas são baseadas no ID do usuário autenticado (`auth.uid()`)
- Tabelas do Renum têm políticas adicionais para compartilhamento de recursos

### Autenticação e Autorização

- **Autenticação**: Gerenciada pelo Supabase Auth
- **Autorização**: Combinação de políticas RLS e verificações no backend
- **Tokens**: JWT para comunicação entre frontend e backend

## Implantação

### VPS (Backend Suna e Backend Renum)

- **Sistema Operacional**: Linux
- **Servidor Web**: Nginx como proxy reverso
- **Gerenciamento de Processos**: Systemd
- **Portas**: 8000 (Suna), 9000 (Renum)

### Vercel (Frontend Renum e Painel Admin)

- **Configuração**: Variáveis de ambiente para apontar para os backends
- **Domínios**: Domínios personalizados para cada aplicação
- **Builds**: Automáticos a partir do repositório Git

## Monitoramento e Logs

- **Logs de Aplicação**: Armazenados em `/var/log/renum-backend` e `/var/log/suna`
- **Logs de Sistema**: Acessíveis via `journalctl -u renum-backend` e `journalctl -u suna`
- **Métricas**: Coletadas pelo Backend Renum e armazenadas na tabela `renum_metrics`
- **Auditoria**: Eventos importantes registrados na tabela `renum_audit_logs`

## Considerações de Manutenção

### Atualizações do Sistema Suna

- Backup do banco de dados antes de atualizações
- Verificação de compatibilidade com o Backend Renum
- Testes de integração após atualizações

### Atualizações do Sistema Renum

- Seguir convenção de prefixos para novas tabelas
- Manter compatibilidade com a estrutura de dados do Suna
- Documentar alterações de esquema

## Recuperação de Desastres

- Backups regulares do banco de dados Supabase
- Backups dos arquivos de configuração na VPS
- Procedimentos documentados para restauração

## Próximos Passos

1. Implementar monitoramento avançado
2. Configurar alertas para falhas
3. Implementar CI/CD para implantação automatizada
4. Expandir documentação para desenvolvedores