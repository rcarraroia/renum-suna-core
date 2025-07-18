# Análise de Backup e Recuperação

Este documento descreve como utilizar o script de análise de backup e recuperação para verificar a configuração de backup dos serviços Renum e Suna na VPS.

## Visão Geral

O script `check_backup_recovery.py` analisa a configuração de backup e recuperação dos serviços Renum e Suna na VPS. Ele verifica:

1. **Estratégia de backup existente**
   - Jobs de cron relacionados a backup
   - Scripts de backup
   - Serviços de backup no Docker Compose
   - Configuração de backup de banco de dados
   - Configuração de backup do Supabase
   - Configuração de backup de volumes Docker

2. **Procedimentos de recuperação**
   - Documentação de procedimentos de recuperação
   - Scripts de restauração

3. **Melhorias necessárias**
   - Identificação de lacunas na estratégia de backup
   - Recomendações para melhorar a configuração de backup

## Pré-requisitos

- Python 3.6+
- Biblioteca paramiko (`pip install paramiko`)
- Acesso SSH à VPS
- Permissões para executar comandos como root na VPS

## Como Executar

### Execução Direta

```bash
python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa
```

### Opções de Linha de Comando

- `--host`: Hostname ou IP da VPS (padrão: 157.180.39.41)
- `--port`: Porta SSH (padrão: 22)
- `--user`: Nome de usuário SSH (padrão: root)
- `--key-file`: Caminho para o arquivo de chave privada SSH
- `--output-dir`: Diretório para salvar os arquivos de saída (padrão: ./output)
- `--containers-file`: Caminho para um arquivo JSON com informações de contêineres (opcional)

### Modo de Teste

Para testar o script sem conectar-se à VPS, você pode usar o script `test_backup_recovery.py`:

```bash
python test_backup_recovery.py --mock
```

Isso criará dados simulados para testar a funcionalidade do script.

## Arquivos de Saída

O script gera os seguintes arquivos no diretório de saída:

- `containers.json`: Informações sobre os contêineres Docker
- `backup_cron_jobs.json`: Jobs de cron relacionados a backup
- `backup_scripts.json`: Scripts de backup encontrados
- `compose_backup_services.json`: Serviços de backup no Docker Compose
- `db_backup_config.json`: Configuração de backup de banco de dados
- `supabase_backup_config.json`: Configuração de backup do Supabase
- `volume_backup_config.json`: Configuração de backup de volumes Docker
- `backup_analysis.json`: Análise da configuração de backup
- `backup_summary.json`: Resumo da análise
- `backup_recovery_report.txt`: Relatório completo em formato texto

## Interpretação dos Resultados

### Status

O status geral da configuração de backup pode ser:

- **OK**: Configuração de backup adequada
- **WARNING**: Configuração de backup com lacunas
- **ERROR**: Configuração de backup inadequada ou inexistente

### Métodos de Backup

O script identifica os seguintes métodos de backup:

- **Cron Jobs**: Jobs de cron configurados para executar backups
- **Backup Scripts**: Scripts dedicados para backup
- **Docker Compose Backup Services**: Serviços de backup definidos no Docker Compose
- **Database Backup**: Configuração de backup específica para bancos de dados
- **Supabase Backup**: Configuração de backup específica para o Supabase
- **Volume Backup**: Configuração de backup para volumes Docker

### Problemas Comuns

O script pode identificar os seguintes problemas:

- **Nenhum método de backup encontrado**: Não há configuração de backup
- **Bancos de dados sem configuração de backup**: Os bancos de dados não têm backup configurado
- **Supabase sem configuração de backup**: O Supabase não tem backup configurado
- **Volumes Docker sem configuração de backup**: Os volumes Docker não têm backup configurado

## Recomendações

Com base na análise, o script fornece recomendações para melhorar a configuração de backup, como:

- Implementar uma estratégia de backup abrangente
- Configurar jobs de cron para executar backups regularmente
- Armazenar backups em local seguro
- Documentar procedimentos de recuperação
- Testar regularmente a restauração de backups

## Exemplo de Relatório

```
=======================================================
RELATÓRIO DE BACKUP E RECUPERAÇÃO - 17/07/2025 10:00:00
=======================================================

MÉTODOS DE BACKUP ENCONTRADOS:
Cron Jobs, Backup Scripts

Backup de banco de dados: ✅ Configurado
Backup do Supabase: ❌ Não configurado
Backup de volumes Docker: ❌ Não configurado

Status: WARNING

DETALHES DE JOBS DE CRON RELACIONADOS A BACKUP:

Crontab do root:
0 2 * * * /usr/local/bin/backup_postgres.sh

SCRIPTS DE BACKUP ENCONTRADOS:
- /usr/local/bin/backup_postgres.sh
- /root/backup_scripts/db_backup.sh

CONFIGURAÇÃO DE BACKUP DE BANCO DE DADOS:

postgres (postgres):
  Jobs de cron:
  - 0 2 * * * pg_dump -U postgres -d mydb > /var/backups/postgres/mydb_$(date +%Y%m%d).sql

PROBLEMAS DETECTADOS:
- Supabase sem configuração de backup
- Volumes Docker sem configuração de backup

RECOMENDAÇÕES:
- Implementar backup regular do Supabase
- Configurar backup de volumes Docker para preservar dados persistentes
- Documentar procedimentos de recuperação para cada tipo de backup
- Testar regularmente a restauração de backups para garantir sua eficácia
- Considerar o uso de ferramentas de backup automatizadas como restic, duplicity ou borgbackup
```

## Próximos Passos

Após executar a análise, recomenda-se:

1. Revisar o relatório gerado
2. Implementar as recomendações sugeridas
3. Documentar os procedimentos de recuperação
4. Testar a restauração de backups
5. Configurar monitoramento para verificar se os backups estão sendo executados corretamente

## Solução de Problemas

### Erro de Conexão SSH

Se você encontrar erros de conexão SSH, verifique:

- Se o host está acessível
- Se as credenciais SSH estão corretas
- Se a chave SSH tem as permissões corretas (600)

### Erro ao Executar Comandos

Se o script não conseguir executar comandos na VPS, verifique:

- Se o usuário tem permissões suficientes
- Se os comandos necessários estão instalados na VPS (docker, find, grep, etc.)

### Dados Incompletos

Se o relatório estiver incompleto, verifique:

- Se todos os contêineres estão em execução
- Se o usuário tem acesso a todos os diretórios necessários