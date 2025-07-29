# Otimização do Sistema Operacional para WebSocket

Este módulo implementa otimizações automáticas do sistema operacional para suportar alta concorrência de conexões WebSocket, resolvendo problemas como "Insufficient resources" e conexões fechadas prematuramente.

## 🎯 Objetivo

Diagnosticar e corrigir limitações do sistema operacional que impedem o funcionamento adequado de conexões WebSocket em alta escala, incluindo:

- Limites de file descriptors insuficientes
- Configurações TCP inadequadas
- Limites de memória restritivos
- Configurações de rede não otimizadas

## 📁 Arquivos Principais

### `utils/system_optimizer.py`
Classe principal que implementa:
- **SystemOptimizer**: Diagnóstica e aplica otimizações
- **SystemLimit**: Representa limites do sistema
- **OptimizationResult**: Resultado de otimizações aplicadas

### Scripts de Execução

- **`optimize_system.py`**: Script principal para otimizar o sistema
- **`test_system_optimization.py`**: Testes de validação das otimizações
- **`monitor_websocket_resources.py`**: Monitor em tempo real de recursos
- **`demo_system_optimization.py`**: Demonstração completa do processo

## 🚀 Como Usar

### 1. Diagnóstico e Otimização Básica

```bash
# Execução básica (sem privilégios de root)
python3 backend/optimize_system.py

# Execução com privilégios (recomendado)
sudo python3 backend/optimize_system.py
```

### 2. Testes de Validação

```bash
# Executa todos os testes de validação
python3 backend/test_system_optimization.py
```

### 3. Monitoramento de Recursos

```bash
# Monitor contínuo (atualiza a cada 5 segundos)
python3 backend/monitor_websocket_resources.py

# Monitor com intervalo personalizado (10 segundos)
python3 backend/monitor_websocket_resources.py 10

# Verificação única
python3 backend/monitor_websocket_resources.py --once
```

### 4. Demonstração Completa

```bash
# Executa todo o processo de otimização
python3 backend/demo_system_optimization.py
```

## 🔧 Otimizações Implementadas

### File Descriptors
- **Problema**: Limite padrão muito baixo (1024)
- **Solução**: Aumenta para 65536
- **Arquivo**: `/etc/security/limits.d/99-websocket-limits.conf`

### Configurações TCP
- **tcp_max_syn_backlog**: Aumenta para 8192
- **tcp_keepalive_time**: Otimiza para 600 segundos
- **tcp_fin_timeout**: Reduz para 30 segundos

### Configurações de Rede
- **net.core.somaxconn**: Aumenta para 8192
- **net.core.netdev_max_backlog**: Aumenta para 5000

### Configurações de Memória
- **vm.max_map_count**: Aumenta para 262144
- **kernel.shmmax**: Configura para 1GB

## 📊 Monitoramento

O sistema de monitoramento acompanha:

### Métricas em Tempo Real
- **CPU**: Uso percentual e load average
- **Memória**: Uso total e disponível
- **File Descriptors**: Uso atual vs limites
- **Conexões**: TCP total, WebSocket específicas
- **Rede**: Throughput e pacotes

### Alertas Automáticos
- CPU > 80%
- Memória > 85%
- File Descriptors > 90%
- Conexões WebSocket > 500
- Load average > 4.0

### Relatórios
- **Texto**: Relatório legível com estatísticas
- **JSON**: Dados completos para análise
- **Histórico**: Mantém últimas 100 medições

## 🧪 Testes de Validação

### Testes Implementados

1. **File Descriptors**: Verifica limites adequados
2. **Memória**: Confirma disponibilidade suficiente
3. **TCP**: Valida configurações otimizadas
4. **Rede**: Testa configurações de rede
5. **Conexões**: Simula abertura de múltiplas conexões
6. **Performance**: Avalia performance geral

### Critérios de Aprovação

- File descriptors ≥ 10.000
- Memória disponível ≥ 2GB
- Configurações TCP otimizadas
- Capacidade ≥ 500 conexões simultâneas
- CPU < 80% em repouso

## 📋 Relatórios Gerados

### `system_optimization_report.txt`
Relatório detalhado com:
- Diagnóstico de limites atuais
- Otimizações aplicadas
- Problemas críticos identificados
- Recomendações específicas

### `system_optimization_test_report.txt`
Resultado dos testes com:
- Status de cada teste
- Métricas coletadas
- Recomendações de correção

### `websocket_monitoring_*.json`
Dados de monitoramento com:
- Métricas históricas
- Estatísticas calculadas
- Timestamps detalhados

## ⚠️ Requisitos e Limitações

### Sistemas Suportados
- **Linux**: Suporte completo
- **macOS**: Suporte parcial
- **Windows**: Limitado (apenas diagnóstico)

### Privilégios Necessários
- **Root/Admin**: Para aplicar otimizações
- **Usuário normal**: Apenas diagnóstico

### Dependências
```bash
pip install psutil
```

## 🔄 Configurações Persistentes

### Linux - Systemd
As otimizações criam arquivos de configuração persistentes:

```bash
# Limites de file descriptors
/etc/security/limits.d/99-websocket-limits.conf

# Configurações sysctl
/etc/sysctl.d/99-websocket-optimizations.conf
```

### Aplicação Manual
```bash
# Recarrega configurações sysctl
sudo sysctl -p /etc/sysctl.d/99-websocket-optimizations.conf

# Verifica limites aplicados
ulimit -n
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **"Permission denied"**
   - Execute como root/administrador
   - Verifique permissões dos arquivos

2. **"Insufficient resources" persiste**
   - Reinicie o sistema após otimizações
   - Verifique se configurações foram aplicadas
   - Execute testes de validação

3. **Otimizações não aplicadas**
   - Confirme privilégios adequados
   - Verifique logs de erro
   - Execute diagnóstico novamente

### Verificação Manual
```bash
# Verifica file descriptors
ulimit -n

# Verifica configurações sysctl
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog

# Monitora conexões
netstat -an | grep :8000 | wc -l
```

## 📈 Métricas de Sucesso

### Antes da Otimização
- File descriptors: 1024
- Conexões simultâneas: ~100
- Erros "Insufficient resources": Frequentes
- CPU sob carga: >90%

### Após Otimização
- File descriptors: 65536
- Conexões simultâneas: >500
- Erros "Insufficient resources": Eliminados
- CPU sob carga: <70%

## 🔮 Próximos Passos

1. **Monitoramento Contínuo**: Acompanhe métricas em produção
2. **Ajuste Fino**: Otimize baseado em padrões de uso
3. **Escalabilidade**: Configure auto-scaling baseado em métricas
4. **Alertas**: Implemente notificações proativas

## 📞 Suporte

Para problemas específicos:
1. Execute `demo_system_optimization.py` para diagnóstico completo
2. Revise logs em `backend/system_optimization_report.txt`
3. Use monitor em tempo real para identificar gargalos
4. Consulte seção de troubleshooting acima