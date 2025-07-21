# Mudanças de Diretório

Este documento registra as alterações feitas para refletir a renomeação dos diretórios `backend` para `backend` e `frontend` para `Suna frontend`.

## Arquivos Atualizados

1. **docker-compose.yaml**
   - Atualizado todos os caminhos de `./backend` para `./backend`
   - Atualizado todos os caminhos de `./frontend` para `./Suna frontend`

2. **start.py**
   - Atualizado instruções de inicialização manual para usar os novos nomes de diretórios
   - Alterado `cd frontend` para `cd "Suna frontend"`
   - Alterado `cd backend` para `cd "backend"`

3. **.github/workflows/docker-build.yml**
   - Atualizado o contexto de build de `./backend` para `./backend`
   - Atualizado o caminho do Dockerfile de `./backend/Dockerfile` para `./backend/Dockerfile`

## Verificações Adicionais

Os seguintes arquivos também foram verificados e já estavam atualizados ou não precisavam de alterações:

1. **setup.py**
   - Já estava atualizado para usar os novos nomes de diretórios

## Próximos Passos

1. **Verificar Importações em Código**
   - Verificar se há importações em código Python que referenciam os diretórios antigos
   - Atualizar quaisquer importações que usem caminhos absolutos

2. **Verificar Scripts de Implantação**
   - Verificar se há scripts de implantação adicionais que referenciam os diretórios antigos
   - Atualizar quaisquer scripts que usem caminhos absolutos

3. **Verificar Documentação**
   - Atualizar qualquer documentação que referencie os diretórios antigos

## Observações

A renomeação dos diretórios foi feita para manter uma separação clara entre os componentes da Plataforma Suna e os da Plataforma Renum dentro do mono-repositório, conforme o plano de desenvolvimento aprovado.
