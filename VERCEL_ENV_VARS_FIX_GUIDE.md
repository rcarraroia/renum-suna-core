# 🔧 Guia de Correção - Variáveis de Ambiente no Vercel

## 🚨 Problema Identificado

O diagnóstico confirmou que as variáveis de ambiente **não estão sendo aplicadas no Vercel**:

```
NEXT_PUBLIC_API_URL: http://localhost:8000 (❌ deveria ser produção)
NEXT_PUBLIC_WEBSOCKET_URL: ws://localhost:8000/ws (❌ deveria ser produção)
```

## 🎯 Solução Passo a Passo

### 1. **Acessar Dashboard do Vercel**
1. Acesse [vercel.com](https://vercel.com)
2. Faça login na sua conta
3. Selecione o projeto `renum-frontend`

### 2. **Configurar Variáveis de Ambiente**
1. Vá em **Settings** → **Environment Variables**
2. Adicione/edite as seguintes variáveis:

#### Para Produção (Production):
```env
NEXT_PUBLIC_API_URL=https://api.renum.com.br
NEXT_PUBLIC_WEBSOCKET_URL=wss://api.renum.com.br/ws
```

#### OU (se usando IP direto):
```env
NEXT_PUBLIC_API_URL=https://157.180.39.41:8000
NEXT_PUBLIC_WEBSOCKET_URL=wss://157.180.39.41:9000/ws
```

### 3. **Configuração Detalhada no Vercel**

Para cada variável:
- **Key**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://api.renum.com.br` (ou IP com porta)
- **Environment**: Selecionar **Production** ✅
- Clicar em **Save**

Repetir para:
- **Key**: `NEXT_PUBLIC_WEBSOCKET_URL`
- **Value**: `wss://api.renum.com.br/ws` (ou IP com porta)
- **Environment**: Selecionar **Production** ✅

### 4. **Fazer Redeploy**
1. Vá em **Deployments**
2. Clique nos **3 pontos** do último deployment
3. Selecione **Redeploy**
4. Aguardar o build completar

## ⚠️ Pontos Importantes

### WebSocket SSL (WSS)
O WebSocket **DEVE** usar `wss://` (não `ws://`) porque:
- O frontend está em HTTPS (Vercel)
- Navegadores bloqueiam WebSocket inseguro em páginas HTTPS
- Isso causa o erro "Mixed Content"

### Backend SSL
Para que `wss://` funcione, o backend precisa:
- **Certificado SSL** configurado na porta WebSocket
- **OU** proxy reverso com SSL (nginx, cloudflare)
- **OU** usar serviço como Let's Encrypt

## 🧪 Validação Após Correção

### 1. Verificar Variáveis
Após redeploy, verificar no console do navegador:
```javascript
console.log('API:', process.env.NEXT_PUBLIC_API_URL);
console.log('WS:', process.env.NEXT_PUBLIC_WEBSOCKET_URL);
```

### 2. Testar Conectividade
```bash
# Testar API
curl -I https://api.renum.com.br/api/health

# Testar WebSocket SSL
openssl s_client -connect api.renum.com.br:443
```

### 3. Verificar Logs
- Não deve mais aparecer `localhost:8000` nos logs
- Não deve mais aparecer "Mixed Content" errors

## 🔄 Configurações Alternativas

### Opção 1: Domínio Personalizado
```env
NEXT_PUBLIC_API_URL=https://api.renum.com.br
NEXT_PUBLIC_WEBSOCKET_URL=wss://api.renum.com.br/ws
```

### Opção 2: IP Direto com SSL
```env
NEXT_PUBLIC_API_URL=https://157.180.39.41:8000
NEXT_PUBLIC_WEBSOCKET_URL=wss://157.180.39.41:9000/ws
```

### Opção 3: IP Direto sem SSL (Temporário)
⚠️ **Não recomendado** - causará Mixed Content errors
```env
NEXT_PUBLIC_API_URL=http://157.180.39.41:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://157.180.39.41:9000/ws
```

## 📋 Checklist de Verificação

- [ ] Variáveis adicionadas no Vercel Dashboard
- [ ] Environment definido como "Production"
- [ ] Redeploy realizado
- [ ] URLs usando HTTPS/WSS
- [ ] Backend suportando SSL (se necessário)
- [ ] Teste de conectividade realizado
- [ ] Logs verificados (sem localhost)

## 🚀 Próximos Passos

1. **Configurar variáveis no Vercel** (prioridade máxima)
2. **Fazer redeploy** da aplicação
3. **Configurar SSL no backend** (se necessário)
4. **Testar em produção**
5. **Monitorar logs** para confirmar correção

## 📞 Suporte Backend

Se o backend não suportar SSL:
1. **Configurar certificado SSL** no servidor
2. **OU** usar proxy reverso (nginx + Let's Encrypt)
3. **OU** usar serviços como Cloudflare para SSL

---

**Status**: 🔴 **AÇÃO NECESSÁRIA**
**Prioridade**: 🚨 **CRÍTICA**
**Tempo Estimado**: 15-30 minutos