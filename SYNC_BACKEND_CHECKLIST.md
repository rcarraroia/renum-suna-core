# Checklist de Sincronização do Backend

Use esta checklist para garantir que todas as etapas necessárias sejam concluídas durante o processo de sincronização do backend com o repositório oficial do Suna.

## Preparação

- [ ] Fazer backup completo do repositório
- [ ] Identificar e documentar pontos de integração entre o backend do Suna e o Renum
- [ ] Executar testes para estabelecer uma linha de base
- [ ] Verificar se há alterações locais não commitadas no diretório backend

## Configuração

- [ ] Adicionar o repositório oficial do Suna como remote (`git remote add suna-upstream https://github.com/kortix-ai/suna.git`)
- [ ] Verificar se o remote foi adicionado corretamente (`git remote -v`)
- [ ] Buscar as atualizações do repositório oficial (`git fetch suna-upstream`)
- [ ] Criar um branch temporário para a sincronização (`git checkout -b sync-backend-temp`)

## Sincronização

- [ ] Obter as atualizações do diretório backend (`git checkout suna-upstream/main -- backend`)
- [ ] Verificar as alterações aplicadas (`git status`)
- [ ] Identificar e documentar conflitos (se houver)
- [ ] Resolver conflitos priorizando a manutenção das integrações com o Renum

## Verificação de Alterações Críticas

- [ ] Verificar alterações em `requirements.txt` ou `pyproject.toml`
- [ ] Verificar alterações em arquivos de configuração (`.env.example`, etc.)
- [ ] Verificar alterações em APIs utilizadas pelo Renum
- [ ] Verificar alterações em modelos de dados
- [ ] Verificar alterações em serviços e utilitários utilizados pelo Renum

## Testes

- [ ] Executar testes unitários
- [ ] Executar testes de integração
- [ ] Verificar integrações específicas entre o backend do Suna e o Renum
- [ ] Corrigir problemas identificados durante os testes
- [ ] Executar testes novamente após correções

## Finalização

- [ ] Commitar as alterações no branch temporário (`git add backend && git commit -m "Sync backend with official Suna repository"`)
- [ ] Mesclar as alterações no branch principal (`git checkout main && git merge sync-backend-temp`)
- [ ] Resolver conflitos de merge (se houver)
- [ ] Executar testes finais para garantir que tudo está funcionando corretamente
- [ ] Documentar o processo de sincronização e as alterações feitas

## Documentação

- [ ] Criar um relatório detalhado das alterações feitas
- [ ] Documentar quaisquer problemas encontrados e como foram resolvidos
- [ ] Registrar as versões dos repositórios envolvidos
- [ ] Atualizar a documentação do projeto conforme necessário

## Verificação Pós-Sincronização

- [ ] Verificar se todas as integrações com o Renum estão funcionando corretamente
- [ ] Verificar se não há regressões em funcionalidades existentes
- [ ] Verificar se novas funcionalidades do backend do Suna estão funcionando corretamente
- [ ] Verificar se as configurações personalizadas foram mantidas