# 🚀 Scripts de Deploy Automático

Esta pasta contém todos os scripts necessários para configurar e gerenciar o deploy automático dos backends Suna e Renum.

## 📁 Arquivos Incluídos

### Scripts de Configuração
- `setup-vps-deploy.sh` - Configuração inicial da VPS
- `github-secrets-helper.sh` - Helper para configurar secrets do GitHub

### Scripts de Deploy Manual
- `manual-deploy-suna.sh` - Deploy manual do Suna Backend
- `manual-deploy-renum.sh` - Deploy manual do Renum Backend

### Scripts de Monitoramento
- `validate-deployment.sh` - Validar configuração de deploy
- `monitor-deployment.sh` - Monitor em tempo real dos serviços

### Scripts de Emergência
- `rollback.sh` - Rollback para versões anteriores

## 🔧 Ordem de Execução

### 1. Configuração Inicial (Execute NA VPS)
```bash
# Baixar e executar setup
wget https://raw.githubusercontent.com/seu-repo/scripts/deploy/setup-vps-deploy.sh
chmod +x setup-vps-deploy.sh
./setup-vps-deploy.sh
```

### 2. Configurar GitHub Secrets
```bash
# Obter informações para secrets
./github-secrets-helper.sh
```

### 3. Teste Manual
```bash
# Testar deploy manual primeiro
./manual-deploy-suna.sh
./manual-deploy-renum.sh
```

### 4. Validação
```bash
# Validar toda a configuração
./validate-deployment.sh
```

### 5. Monitoramento
```bash
# Monitorar serviços em tempo real
./monitor-deployment.sh
```

## 🚨 Em Caso de Problemas

### Rollback de Emergência
```bash
# Voltar para versão anterior
./rollback.sh
```

### Logs Detalhados
```bash
# Ver logs dos serviços
sudo journalctl -u suna-backend -f
sudo journalctl -u renum-backend -f
```

### Restart Manual
```bash
# Reiniciar serviços
sudo systemctl restart suna-backend
sudo systemctl restart renum-backend
```

## 📋 Checklist de Implementação

### ✅ Pré-requisitos
- [ ] VPS com Ubuntu/Debian
- [ ] Acesso sudo na VPS
- [ ] Repositório no GitHub (renum-suna-core)
- [ ] Domínio configurado (api.renum.com.br)

### ✅ Configuração VPS
- [ ] Executar `setup-vps-deploy.sh`
- [ ] Clonar repositório renum-suna-core
- [ ] Configurar ambientes Python nos subdiretórios
- [ ] Configurar arquivos .env

### ✅ GitHub
- [ ] Adicionar workflows aos repositórios
- [ ] Configurar secrets (usar `github-secrets-helper.sh`)
- [ ] Testar conectividade SSH

### ✅ Nginx
- [ ] Configurar proxy reverso
- [ ] Configurar SSL com Certbot
- [ ] Testar configuração

### ✅ Testes
- [ ] Deploy manual funcionando
- [ ] Validação passou (`validate-deployment.sh`)
- [ ] Health checks OK
- [ ] Deploy automático funcionando

## 🔐 Segurança

### Usuário Deploy
- Acesso limitado apenas aos diretórios necessários
- Chave SSH sem senha
- Sudo apenas para restart de serviços

### Firewall
- SSH (porta 22)
- HTTP (porta 80)
- HTTPS (porta 443)

### Backups
- Backup automático antes de cada deploy
- Rollback disponível em caso de problemas

## 📊 Monitoramento

### Health Checks
- Verificação automática após deploy
- Endpoints `/health` ou raiz
- Timeout configurável

### Logs
- Logs estruturados dos deployments
- Integração com systemd journal
- Alertas em caso de falha

### Métricas
- Status dos serviços
- Uso de recursos (CPU, memória, disco)
- Tempo de resposta

## 🛠️ Personalização

### Portas
- Suna Backend: 8000
- Renum Backend: 9000 (WebSocket)
- Altere nos workflows se necessário

### Branches
- Deploy automático em push para `main` ou `master`
- Configurável nos workflows

### Diretórios
- Repositório principal: `/var/www/renum-suna-core`
- Suna Backend: `/var/www/renum-suna-core/backend`
- Renum Backend: `/var/www/renum-suna-core/renum-backend`
- Altere nos scripts se necessário

## 📞 Suporte

### Logs Úteis
```bash
# Logs dos workflows GitHub Actions
# Ver no GitHub: Actions → Workflow → Logs

# Logs dos serviços
sudo journalctl -u suna-backend -f
sudo journalctl -u renum-backend -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Comandos de Diagnóstico
```bash
# Status dos serviços
sudo systemctl status suna-backend renum-backend

# Portas abertas
sudo netstat -tlnp | grep -E ':(8000|9000) '

# Processos Python
ps aux | grep python

# Uso de recursos
htop
```

---

**🎯 Tudo configurado e pronto para usar!**

Para dúvidas ou problemas, consulte o `DEPLOY_AUTOMATION_GUIDE.md` principal.