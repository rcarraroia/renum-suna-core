# 🚀 Guia Completo de Deploy Automático - Suna & Renum

Este guia te ajudará a configurar deploy automático para os backends Suna e Renum na sua VPS.

## 📋 Pré-requisitos

- VPS com Ubuntu/Debian
- Acesso root ou sudo na VPS
- Repositório Git no GitHub (renum-suna-core)
- Domínio configurado (api.renum.com.br)

## 🔧 Passo 1: Configuração na VPS

### 1.1 Execute o script de configuração

```bash
# Na VPS, como usuário não-root
wget https://raw.githubusercontent.com/seu-repo/scripts/deploy/setup-vps-deploy.sh
chmod +x setup-vps-deploy.sh
./setup-vps-deploy.sh
```

### 1.2 Clone o repositório

```bash
# Como usuário deploy
sudo su - deploy

# Clone do repositório principal
cd /var/www
git clone https://github.com/rcarraroia/renum-suna-core.git
```

### 1.3 Configure os ambientes

```bash
# Suna Backend
cd /var/www/renum-suna-core/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure o .env com suas variáveis

# Renum Backend
cd /var/www/renum-suna-core/renum-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure o .env com suas variáveis
```

## 🔐 Passo 2: Configuração dos GitHub Secrets

Vá para cada repositório no GitHub → Settings → Secrets and variables → Actions

### Secrets necessários:

```
VPS_HOST: [IP_DA_SUA_VPS]
VPS_USER: deploy
VPS_PORT: 22
VPS_SSH_KEY: [CHAVE_PRIVADA_SSH_GERADA]
```

### Como obter a chave SSH:

```bash
# Na VPS, como usuário deploy
cat /home/deploy/.ssh/deploy_key
```

Copie TODO o conteúdo (incluindo -----BEGIN e -----END) para o secret `VPS_SSH_KEY`.

## 🧪 Passo 3: Teste Manual

Antes de ativar o deploy automático, teste manualmente:

```bash
# Na VPS, como usuário deploy
cd /var/www/renum-suna-core
./scripts/deploy/manual-deploy-suna.sh
./scripts/deploy/manual-deploy-renum.sh
```

## ⚙️ Passo 4: Verificação do Nginx

O Nginx já está configurado e funcionando como proxy reverso para api.renum.com.br com SSL/TLS ativo. A configuração atual:

- **Domínio**: api.renum.com.br (HTTPS/WSS)
- **Suna Backend**: Proxy para localhost:8000
- **Renum Backend**: Proxy para localhost:9000 (WebSocket)
- **SSL**: Já configurado com Certbot

**Não é necessário alterar a configuração do Nginx.** Se precisar verificar:

```bash
# Verificar configuração atual
sudo nginx -t
sudo systemctl status nginx

# Ver configuração ativa
sudo cat /etc/nginx/sites-enabled/default
```

## 🔄 Passo 5: Ativação do Deploy Automático

### 5.1 Estrutura dos Workflows

Os workflows já foram criados em:
- `.github/workflows/deploy-suna-backend.yml`
- `.github/workflows/deploy-renum-backend.yml`

### 5.2 Como funciona

1. **Trigger**: Push para branch `main` ou `master`
2. **Build**: Instala dependências e roda testes
3. **Deploy**: Conecta via SSH e atualiza o código
4. **Restart**: Reinicia o serviço automaticamente
5. **Health Check**: Verifica se está funcionando

### 5.3 Monitoramento

Os workflows incluem:
- ✅ Backup automático antes do deploy
- 🔄 Restart inteligente (detecta systemd/PM2/Docker)
- 🏥 Health checks
- 📝 Logs detalhados
- 🚨 Notificações de status

## 🛠️ Comandos Úteis

### Verificar status dos serviços:
```bash
sudo systemctl status suna-backend
sudo systemctl status renum-backend
```

### Ver logs:
```bash
sudo journalctl -u suna-backend -f
sudo journalctl -u renum-backend -f
```

### Restart manual:
```bash
sudo systemctl restart suna-backend
sudo systemctl restart renum-backend
```

### Verificar portas:
```bash
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8001
```

## 🔒 Segurança

### Firewall configurado para:
- SSH (porta 22)
- HTTP (porta 80)
- HTTPS (porta 443)

### Usuário deploy com:
- Acesso limitado apenas aos diretórios necessários
- Chave SSH sem senha
- Sudo apenas para restart de serviços

## 🚨 Troubleshooting

### Deploy falha?
1. Verifique os logs do GitHub Actions
2. Teste SSH manual: `ssh -i chave deploy@sua-vps`
3. Verifique se os serviços estão rodando
4. Confira os logs dos serviços

### Serviço não inicia?
1. Verifique o arquivo `.env`
2. Confira as dependências Python
3. Veja os logs: `sudo journalctl -u nome-servico -f`

### Health check falha?
1. Verifique se a porta está aberta
2. Teste local: `curl http://localhost:8000`
3. Confira configuração do Nginx

## 📞 Próximos Passos

1. ✅ Configure SSL com Certbot
2. ✅ Configure monitoramento (Prometheus/Grafana)
3. ✅ Configure alertas de falha
4. ✅ Configure backup automático do banco

---

## 🎯 Resumo dos Arquivos Criados

- `.github/workflows/deploy-suna-backend.yml` - Workflow Suna
- `.github/workflows/deploy-renum-backend.yml` - Workflow Renum  
- `scripts/deploy/setup-vps-deploy.sh` - Setup inicial VPS
- `scripts/deploy/manual-deploy-suna.sh` - Deploy manual Suna
- `scripts/deploy/manual-deploy-renum.sh` - Deploy manual Renum

**Tudo pronto para implementar! 🚀**