# Checklist de Verificação da Integração Renum-Suna

Use este checklist para verificar se a integração entre o backend Renum e o sistema Suna foi realizada com sucesso.

## 1. Configuração do Ambiente

- [ ] Backend Renum instalado em `/opt/renum-backend`
- [ ] Ambiente virtual Python configurado
- [ ] Arquivo `.env` configurado corretamente
- [ ] Dependências instaladas

## 2. Banco de Dados Supabase

- [ ] Conexão com o Supabase estabelecida
- [ ] Tabela `renum_agent_shares` criada
- [ ] Tabela `renum_settings` criada
- [ ] Tabela `renum_metrics` criada
- [ ] Tabela `renum_audit_logs` criada
- [ ] Políticas RLS aplicadas corretamente

## 3. Serviço Systemd

- [ ] Arquivo de serviço `/etc/systemd/system/renum-backend.service` criado
- [ ] Serviço habilitado para iniciar automaticamente
- [ ] Serviço em execução
- [ ] Logs do serviço acessíveis via `journalctl -u renum-backend`

## 4. Configuração do NGINX

- [ ] Arquivo de configuração `/etc/nginx/sites-available/renum-backend` criado
- [ ] Link simbólico em `/etc/nginx/sites-enabled/` criado
- [ ] Configuração do NGINX válida (`nginx -t`)
- [ ] NGINX reiniciado após configuração
- [ ] Logs do NGINX configurados e acessíveis

## 5. Comunicação entre Backends

- [ ] Backend Renum acessível via `http://localhost:9000/health`
- [ ] Backend Suna acessível via `http://localhost:8000/health`
- [ ] Proxy reverso do NGINX funcionando corretamente
- [ ] API acessível via `https://api.renum.com.br/api/v2/` (ou domínio configurado)

## 6. Segurança

- [ ] Firewall configurado para permitir apenas portas necessárias
- [ ] HTTPS configurado (se aplicável)
- [ ] Permissões de arquivos e diretórios configuradas corretamente
- [ ] Variáveis de ambiente sensíveis protegidas

## 7. Backup e Recuperação

- [ ] Backup do sistema original criado
- [ ] Procedimento de backup regular configurado
- [ ] Procedimento de recuperação documentado e testado

## 8. Monitoramento

- [ ] Logs centralizados configurados
- [ ] Monitoramento de recursos configurado
- [ ] Alertas configurados para falhas

## 9. Frontend Renum

- [ ] Frontend configurado para apontar para a API correta
- [ ] Frontend implantado no Vercel
- [ ] Comunicação entre frontend e backend testada

## 10. Testes Finais

- [ ] Login e autenticação funcionando
- [ ] Criação de agentes funcionando
- [ ] Compartilhamento de agentes funcionando
- [ ] Execução de agentes funcionando
- [ ] Integração com o sistema Suna funcionando

## Notas e Observações

Use este espaço para registrar quaisquer problemas encontrados, soluções aplicadas ou observações importantes durante o processo de integração.

```
[Suas notas aqui]
```

## Próximos Passos

- [ ] Desenvolver o painel administrativo
- [ ] Implementar funcionalidades adicionais
- [ ] Configurar monitoramento e alertas
- [ ] Configurar backup automático

---

**Data de verificação:** ____/____/________

**Verificado por:** ____________________

**Assinatura:** ____________________