# Documento Técnico de Ajustes do Sistema Suna-Core e Renum (Kiro Dev)

## Objetivo

Este documento descreve de forma detalhada e pragmática todas as correções, ajustes e melhorias necessárias para estabilizar e preparar o sistema Suna-Core e Renum para operação contínua em ambiente de produção, respeitando a metodologia de desenvolvimento da plataforma Kiro.

---

## 1. Padronização de Dependências e Bibliotecas

### 1.1 Unificação do Redis

- **Problema**: Uso misto de `aioredis` (deprecated) e `redis.asyncio`.
- **Solução**:
  - Remover todas as referências a `aioredis`.
  - Substituir por `redis.asyncio` com `from redis.asyncio import Redis`.
  - Atualizar `requirements.txt` com:
    ```txt
    redis>=5.0.0
    ```
  - Testar funcionalidades Pub/Sub e cache após substituição.

### 1.2 Versões Padronizadas

- **Problema**: Versões diferentes de FastAPI, Supabase, PyJWT, etc.
- **Solução**:
  - Criar `pyproject.toml` ou consolidar dependências nos `requirements.txt`.
  - Versões sugeridas:
    ```toml
    fastapi==0.115.12
    uvicorn==0.27.1
    supabase==2.17.0
    pyjwt==2.10.1
    cryptography==45.0.5
    ```
  - Executar `kiro test` após atualização para validar compatibilidade.

---

## 2. Configuração de Infraestrutura

### 2.1 Otimização do Redis (redis.conf)

- Substituir configuração básica por:
  ```conf
  maxmemory 2gb
  maxmemory-policy allkeys-lru
  appendonly yes
  appendfsync everysec
  requirepass senha_segura
  timeout 120
  loglevel warning
  ```
- Local do arquivo: `backend/services/docker/redis.conf`

### 2.2 Workers no Backend

- Atualizar Dockerfile do `renum-backend`:
  ```dockerfile
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
  ```

### 2.3 Limites de Recursos (docker-compose.yaml)

- Adicionar:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
  ```

---

## 3. Banco de Dados e Supabase

### 3.1 Nomenclatura

- Padronizar prefixos das tabelas com `renum_`.
- Criar migração com `ALTER TABLE` para renomear onde necessário.

### 3.2 Segurança RLS

- Revisar se todas as tabelas possuem políticas ativas de Row Level Security.
- Verificar uso correto de funções do `basejump` para controle de acesso.

---

## 4. Observabilidade e Monitoramento

### 4.1 Prometheus + Grafana

- Instrumentar métricas em FastAPI:
  ```python
  from prometheus_client import Counter
  REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
  ```
- Configurar endpoints `/metrics` nos serviços.
- Criar dashboard no Grafana conectado ao Prometheus.

### 4.2 Sentry

- Validar configuração ativa nos serviços para logging e rastreamento.

---

## 5. Frontend e Admin

### 5.1 Sincronização de Dependências

- Alinhar versões do Next.js, Zustand, React Query, Tailwind entre `renum-frontend` e `renum-admin`.
- Rodar `npm install` seguido de `kiro test` para garantir integridade.

### 5.2 Otimizações de Performance

- Implementar `code splitting`, `lazy loading` e compressão de imagens no build de produção.

---

## 6. Testes Automatizados

### 6.1 Backend

- Utilizar `pytest` e cobertura mínima de 80% em endpoints REST principais.

### 6.2 Frontend

- Utilizar `Jest` + `React Testing Library` para páginas críticas.

---

## 7. Documentação Técnica

### 7.1 Uso de MkDocs

- Criar pasta `/docs` com estrutura:
  - `index.md`
  - `backend.md`
  - `frontend.md`
  - `infra.md`
- Publicar via GitHub Pages ou pipeline integrado ao Kiro.

---

## 8. Pipeline CI/CD

### 8.1 Testes + Deploy

- Configurar pipeline Kiro para:
  - Rodar testes automáticos
  - Validar build e lint
  - Deploy para ambiente staging
  - Deploy manual para produção

---

## 9. Checklist Final de Execução (Kiro)

| Etapa                                 | Status |
| ------------------------------------- | ------ |
| Substituir aioredis por redis.asyncio | ☐      |
| Atualizar versões de dependências     | ☐      |
| Revisar redis.conf para produção      | ☐      |
| Dockerfile com múltiplos workers      | ☐      |
| docker-compose com limites de recurso | ☐      |
| Padronizar prefixos das tabelas       | ☐      |
| Implementar métricas Prometheus       | ☐      |
| Sincronizar dependências do frontend  | ☐      |
| Criar testes automatizados            | ☐      |
| Criar documentação técnica MkDocs     | ☐      |

---

## Conclusão

A aplicação Suna-Core e Renum possui uma base sólida, mas precisa dessas correções para garantir estabilidade, segurança, escalabilidade e performance contínua. Todas as ações propostas são compatíveis com a metodologia do Kiro e podem ser realizadas de forma incremental e controlada por equipe técnica capacitada.

---

**Versão do documento:** 1.0\
**Última atualização:** 28/07/2025\
**Responsável:** Luma (Gerente de Projeto ALIAN)

