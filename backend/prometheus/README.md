# Prometheus Monitoring Setup for Suna/Renum Backend

Este diretório contém a configuração completa do sistema de monitoramento Prometheus para o backend Suna/Renum.

## 📋 Visão Geral

O sistema de monitoramento inclui:
- **Prometheus**: Coleta e armazenamento de métricas
- **Grafana**: Visualização de dashboards
- **Alertmanager**: Gerenciamento de alertas
- **Node Exporter**: Métricas do sistema
- **Redis Exporter**: Métricas do Redis (opcional)

## 🚀 Início Rápido

### 1. Pré-requisitos

```bash
# Docker e Docker Compose instalados
docker --version
docker-compose --version

# Python 3.8+ para scripts de gerenciamento
python3 --version
```

### 2. Iniciar o Stack de Monitoramento

```bash
# Usando o script de gerenciamento
python3 setup_prometheus.py start

# Ou usando Docker Compose diretamente
docker-compose -f docker-compose.prometheus.yml up -d
```

### 3. Acessar os Serviços

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

## 📊 Configuração de Métricas

### Endpoint de Métricas

O backend FastAPI expõe métricas no endpoint:
```
GET /api/metrics
```

### Métricas Coletadas

1. **HTTP Requests**:
   - `http_requests_total`: Total de requisições HTTP
   - `http_request_duration_seconds`: Duração das requisições

2. **Database Operations**:
   - `database_queries_total`: Total de queries no banco
   - `database_query_duration_seconds`: Duração das queries

3. **Redis Operations**:
   - `redis_operations_total`: Total de operações Redis
   - `redis_operation_duration_seconds`: Duração das operações

4. **Worker Tasks**:
   - `worker_tasks_total`: Total de tarefas processadas
   - `worker_task_duration_seconds`: Duração das tarefas

5. **Agent Executions**:
   - `agent_executions_total`: Total de execuções de agentes
   - `agent_execution_duration_seconds`: Duração das execuções

6. **LLM Requests**:
   - `llm_requests_total`: Total de requisições para LLMs
   - `llm_request_duration_seconds`: Duração das requisições

7. **System Metrics**:
   - `process_resident_memory_bytes`: Uso de memória
   - `process_cpu_seconds_total`: Uso de CPU

## 🔧 Configuração

### Prometheus (prometheus.yml)

```yaml
# Configuração principal do Prometheus
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'suna-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics'
    scrape_interval: 10s
```

### Alertas (alert_rules.yml)

Regras de alerta configuradas:
- **HighErrorRate**: Taxa de erro > 10%
- **HighResponseTime**: Tempo de resposta > 2s
- **DatabaseConnectionFailure**: Falhas de conexão com BD
- **ServiceDown**: Serviço indisponível

### Alertmanager (alertmanager.yml)

Configuração de notificações:
- **Email**: Para alertas críticos e warnings
- **Slack**: Para alertas críticos (opcional)
- **Routing**: Por severidade e serviço

## 🛠️ Scripts de Gerenciamento

### setup_prometheus.py

Script Python para gerenciar o stack de monitoramento:

```bash
# Iniciar serviços
python3 setup_prometheus.py start

# Parar serviços
python3 setup_prometheus.py stop

# Reiniciar serviços
python3 setup_prometheus.py restart

# Verificar status
python3 setup_prometheus.py status

# Validar configuração
python3 setup_prometheus.py validate

# Testar endpoint de métricas
python3 setup_prometheus.py test --backend-url http://localhost:8000

# Recarregar configuração do Prometheus
python3 setup_prometheus.py reload

# Verificar targets do Prometheus
python3 setup_prometheus.py targets
```

## 📈 Dashboards Grafana

### Dashboards Incluídos

1. **System Overview**:
   - Métricas gerais do sistema
   - CPU, memória, disco
   - Requisições HTTP

2. **Application Metrics**:
   - Performance da aplicação
   - Tempo de resposta
   - Taxa de erro

3. **Database Monitoring**:
   - Performance do banco de dados
   - Queries lentas
   - Conexões ativas

4. **Redis Monitoring**:
   - Performance do cache
   - Hit/miss ratio
   - Operações por segundo

### Importar Dashboards

1. Acesse Grafana: http://localhost:3000
2. Login: admin/admin123
3. Vá para "+" → "Import"
4. Use os dashboards da pasta `grafana/dashboards/`

## 🚨 Alertas

### Configuração de Email

Edite `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'seu-smtp-server:587'
  smtp_from: 'alerts@renum.com.br'
  smtp_auth_username: 'seu-usuario'
  smtp_auth_password: 'sua-senha'
```

### Configuração de Slack

1. Crie um webhook no Slack
2. Edite `alertmanager.yml`:

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/SEU/WEBHOOK/URL'
    channel: '#alerts'
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Serviços não iniciam**:
   ```bash
   # Verificar logs
   docker-compose -f docker-compose.prometheus.yml logs
   
   # Verificar portas em uso
   netstat -tulpn | grep -E ':(9090|3000|9093)'
   ```

2. **Métricas não aparecem**:
   ```bash
   # Testar endpoint diretamente
   curl http://localhost:8000/api/metrics
   
   # Verificar targets no Prometheus
   python3 setup_prometheus.py targets
   ```

3. **Alertas não funcionam**:
   ```bash
   # Verificar configuração do Alertmanager
   python3 setup_prometheus.py validate
   
   # Verificar logs do Alertmanager
   docker logs suna-alertmanager
   ```

### Logs dos Serviços

```bash
# Prometheus
docker logs suna-prometheus

# Grafana
docker logs suna-grafana

# Alertmanager
docker logs suna-alertmanager
```

## 📚 Recursos Adicionais

### Documentação

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

### Queries Úteis

```promql
# Taxa de requisições por minuto
rate(http_requests_total[5m])

# Percentil 95 do tempo de resposta
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Uso de memória em MB
process_resident_memory_bytes / 1024 / 1024

# Taxa de erro
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

## 🔒 Segurança

### Recomendações

1. **Alterar senhas padrão**:
   - Grafana: admin/admin123
   - Configurar autenticação adequada

2. **Configurar HTTPS**:
   - Use reverse proxy (nginx/traefik)
   - Certificados SSL/TLS

3. **Restringir acesso**:
   - Firewall para portas de monitoramento
   - VPN ou rede privada

4. **Backup de dados**:
   - Volumes do Prometheus e Grafana
   - Configurações e dashboards

## 📝 Manutenção

### Tarefas Regulares

1. **Limpeza de dados antigos**:
   - Configurado para 30 dias de retenção
   - Ajustar conforme necessário

2. **Atualização de imagens**:
   ```bash
   docker-compose -f docker-compose.prometheus.yml pull
   docker-compose -f docker-compose.prometheus.yml up -d
   ```

3. **Backup de configurações**:
   ```bash
   # Backup dos volumes
   docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data
   ```

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verificar logs dos containers
2. Consultar documentação oficial
3. Usar o script de diagnóstico: `python3 setup_prometheus.py status`