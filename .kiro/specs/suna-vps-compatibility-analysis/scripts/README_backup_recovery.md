# Verificação e Implementação de Backup e Recuperação

Este diretório contém scripts para verificar e implementar procedimentos de backup e recuperação para os serviços Renum e Suna na VPS.

## Scripts Disponíveis

### 1. Verificação de Backup e Recuperação

O script `check_backup_recovery.py` analisa a configuração atual de backup e recuperação na VPS.

**Uso:**
```bash
python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
```

**Opções:**
- `--host`: Hostname ou IP da VPS (padrão: 157.180.39.41)
- `--port`: Porta SSH (padrão: 22)
- `--user`: Nome de usuário SSH (padrão: root)
- `--key-file`: Caminho para o arquivo de chave privada SSH
- `--output-dir`: Diretório para salvar os arquivos de saída (padrão: ./output)
- `--containers-file`: Caminho para um arquivo JSON com informações de contêineres (opcional)

**Saída:**
O script gera um relatório detalhado sobre a configuração de backup atual, incluindo:
- Métodos de backup encontrados
- Configuração de backup de banco de dados
- Configuração de backup do Supabase
- Configuração de backup de volumes Docker
- Problemas detectados
- Recomendações

### 2. Teste de Verificação de Backup

O script `test_backup_recovery.py` permite testar o script de verificação de backup sem conectar-se à VPS.

**Uso:**
```bash
python test_backup_recovery.py --mock
```

**Opções:**
- `--mock`: Usar dados simulados em vez de conectar-se à VPS
- `--output-dir`: Diretório para salvar os arquivos de saída (padrão: ./output/backup_test)

### 3. Implementação de Solução Básica de Backup

O script `setup_basic_backup.py` configura uma solução básica de backup na VPS.

**Uso:**
```bash
python setup_basic_backup.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
```

**Opções:**
- `--host`: Hostname ou IP da VPS (padrão: 157.180.39.41)
- `--port`: Porta SSH (padrão: 22)
- `--user`: Nome de usuário SSH (padrão: root)
- `--key-file`: Caminho para o arquivo de chave privada SSH
- `--backup-dir`: Diretório para armazenar backups (padrão: /var/backups/renum-suna)
- `--retention-days`: Número de dias para manter backups (padrão: 7)
- `--dry-run`: Simular a execução sem fazer alterações na VPS

**Funcionalidades:**
O script configura:
- Scripts de backup para PostgreSQL, volumes Docker e Supabase
- Jobs de cron para executar backups regularmente
- Script de recuperação para restaurar backups
- Documentação sobre os procedimentos de backup e recuperação

## Fluxo de Trabalho Recomendado

1. **Verificar a configuração atual:**
   ```bash
   python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
   ```

2. **Revisar o relatório gerado** para entender a configuração atual e identificar problemas.

3. **Simular a implementação da solução de backup:**
   ```bash
   python setup_basic_backup.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa --dry-run
   ```

4. **Implementar a solução de backup:**
   ```bash
   python setup_basic_backup.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
   ```

5. **Verificar novamente a configuração** para confirmar que a solução foi implementada corretamente:
   ```bash
   python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
   ```

## Documentação Adicional

Para mais informações sobre a análise de backup e recuperação, consulte o documento:
`../docs/backup_recovery_analysis.md`

## Considerações de Segurança

- **Chaves SSH**: Use chaves SSH com passphrase para autenticação segura
- **Permissões**: Certifique-se de que os diretórios de backup têm permissões restritas (700)
- **Armazenamento Externo**: Configure backups externos para proteção contra falhas do servidor
- **Rotação de Backups**: Mantenha apenas os backups necessários para economizar espaço
- **Testes de Recuperação**: Teste regularmente a recuperação de backups

## Melhorias Futuras

- Implementar backup incremental para reduzir o tamanho dos backups
- Configurar backup automático para o Supabase usando a API oficial
- Implementar verificação automática da integridade dos backups
- Configurar notificações por e-mail para falhas de backup
- Automatizar testes de recuperação