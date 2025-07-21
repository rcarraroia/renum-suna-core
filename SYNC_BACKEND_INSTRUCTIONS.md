# Instruções para Sincronização do Backend

Este documento fornece instruções detalhadas para sincronizar o diretório `backend` do nosso projeto com o repositório oficial do Suna.

## Preparação

Antes de iniciar o processo de sincronização, é importante fazer algumas preparações:

1. **Backup do Repositório**
   - Faça um backup completo do repositório para garantir que você possa reverter em caso de problemas
   - Você pode criar um clone do repositório ou fazer um snapshot do estado atual

2. **Identificar Pontos de Integração**
   - Documente os pontos onde o Renum se integra com o backend do Suna
   - Isso ajudará a identificar áreas que precisam de atenção especial durante a sincronização

3. **Executar Testes**
   - Execute os testes existentes para estabelecer uma linha de base
   - Documente quaisquer falhas existentes para referência futura

## Processo de Sincronização Automatizado

Para facilitar o processo de sincronização, criamos um script que automatiza grande parte das etapas. Você pode executar o script `sync_backend_with_suna.bat` na raiz do repositório.

```bash
.\sync_backend_with_suna.bat
```

O script irá:
1. Verificar se o diretório `backend` existe
2. Adicionar o repositório oficial do Suna como remote
3. Buscar as atualizações do repositório oficial
4. Criar um branch temporário para a sincronização
5. Obter as atualizações do diretório backend
6. Mostrar as alterações aplicadas
7. Fornecer instruções para os próximos passos

## Processo de Sincronização Manual

Se preferir realizar o processo manualmente ou se o script automatizado encontrar problemas, você pode seguir estas etapas:

### 1. Adicionar o Repositório Oficial como Remote

```bash
git remote add suna-upstream https://github.com/kortix-ai/suna.git
```

### 2. Buscar as Atualizações do Repositório Oficial

```bash
git fetch suna-upstream
```

### 3. Criar um Branch Temporário para a Sincronização

```bash
git checkout -b sync-backend-temp
```

### 4. Obter as Atualizações do Diretório Backend

```bash
git checkout suna-upstream/main -- backend
```

### 5. Verificar Alterações e Resolver Conflitos

```bash
git status
```

Se houver conflitos, você precisará resolvê-los manualmente. Preste atenção especial aos arquivos que fazem parte das integrações com o Renum.

### 6. Testar as Alterações

Execute os testes para verificar se tudo está funcionando corretamente após a sincronização.

### 7. Commitar as Alterações

```bash
git add backend
git commit -m "Sync backend with official Suna repository"
```

### 8. Mesclar as Alterações no Branch Principal

```bash
git checkout main
git merge sync-backend-temp
```

## Verificação Pós-Sincronização

Após a sincronização, é importante verificar se tudo está funcionando corretamente:

1. **Executar Testes**
   - Execute todos os testes para garantir que não há regressões
   - Verifique especialmente as integrações entre o backend do Suna e o Renum

2. **Verificar Configurações**
   - Verifique se as configurações personalizadas foram mantidas
   - Verifique se novas configurações foram adicionadas e se precisam ser ajustadas

3. **Documentar Alterações**
   - Documente as alterações feitas durante a sincronização
   - Registre quaisquer problemas encontrados e como foram resolvidos

## Rollback em Caso de Problemas

Se encontrar problemas graves após a sincronização, você pode reverter para o estado anterior:

```bash
git checkout main
git reset --hard HEAD@{1}  # Reverte para o estado anterior ao merge
```

Ou, se estiver usando o branch temporário:

```bash
git checkout main
git branch -D sync-backend-temp  # Remove o branch temporário sem mesclar
```

## Áreas Críticas para Verificar

Durante a sincronização, preste atenção especial a estas áreas:

1. **Dependências**
   - Verifique alterações em `requirements.txt` ou `pyproject.toml`
   - Atualize as dependências conforme necessário

2. **APIs**
   - Verifique se houve mudanças nas APIs utilizadas pelo Renum
   - Adapte o código do Renum se necessário

3. **Configurações**
   - Verifique alterações em arquivos de configuração
   - Atualize as configurações do seu ambiente conforme necessário

4. **Modelos de Dados**
   - Verifique alterações nos modelos de dados
   - Adapte o código do Renum se necessário

## Conclusão

A sincronização do diretório `backend` com o repositório oficial do Suna é um processo importante para manter o sistema atualizado com as últimas correções e melhorias. Seguindo este guia, você pode realizar essa sincronização de forma segura e eficiente, mantendo a integridade das integrações com o Renum.