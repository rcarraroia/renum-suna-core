# Configuração do Ambiente para o Backend Suna

Este documento descreve como configurar o ambiente para o backend do Suna após a sincronização com o repositório oficial.

## Requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes do Python)
- Acesso à internet para baixar dependências

## Scripts Disponíveis

Foram criados vários scripts para facilitar a configuração e gerenciamento do ambiente:

1. **manage_backend.bat**: Script principal que permite escolher qual operação realizar
2. **setup_python_env.bat**: Configura o ambiente Python, cria um ambiente virtual e instala as dependências
3. **check_env_vars.bat**: Verifica se as variáveis de ambiente necessárias estão configuradas
4. **run_tests.bat**: Executa os testes do backend
5. **start_backend.bat**: Inicia o backend
6. **start_worker.bat**: Inicia o worker em segundo plano

## Instruções de Uso

### 1. Configuração Inicial

1. Certifique-se de ter Python 3.11+ instalado:
   - Baixe e instale Python 3.11+ do site oficial: https://www.python.org/downloads/
   - Durante a instalação, marque a opção "Add Python to PATH"

2. Execute o script principal:
   ```
   manage_backend.bat
   ```

3. Escolha a opção 1 para configurar o ambiente Python:
   - O script verificará se Python 3.11+ está instalado
   - Instalará o gerenciador de pacotes uv
   - Criará um ambiente virtual
   - Instalará as dependências
   - Configurará as variáveis de ambiente

### 2. Verificação de Variáveis de Ambiente

1. Execute o script principal:
   ```
   manage_backend.bat
   ```

2. Escolha a opção 2 para verificar as variáveis de ambiente:
   - O script comparará o arquivo `.env` com o arquivo `.env.example`
   - Mostrará quais variáveis podem estar faltando no seu arquivo `.env`
   - Mostrará quais variáveis estão no seu arquivo `.env` mas não estão em `.env.example`

3. Edite o arquivo `backend/.env` para adicionar as variáveis faltantes

### 3. Execução de Testes

1. Execute o script principal:
   ```
   manage_backend.bat
   ```

2. Escolha a opção 3 para executar os testes:
   - O script ativará o ambiente virtual
   - Executará os testes do backend
   - Desativará o ambiente virtual

### 4. Iniciar o Backend

1. Execute o script principal:
   ```
   manage_backend.bat
   ```

2. Escolha a opção 4 para iniciar o backend:
   - O script ativará o ambiente virtual
   - Iniciará o backend
   - Desativará o ambiente virtual quando o backend for encerrado

### 5. Iniciar o Worker

1. Execute o script principal:
   ```
   manage_backend.bat
   ```

2. Escolha a opção 5 para iniciar o worker:
   - O script ativará o ambiente virtual
   - Iniciará o worker
   - Desativará o ambiente virtual quando o worker for encerrado

## Solução de Problemas

### Problema: Python 3.11+ não está instalado

**Solução**: Baixe e instale Python 3.11+ do site oficial: https://www.python.org/downloads/

### Problema: Falha ao instalar dependências

**Solução**: Tente instalar as dependências manualmente:
```
cd backend
pip install -e .
```

### Problema: Variáveis de ambiente faltando

**Solução**: Edite o arquivo `backend/.env` para adicionar as variáveis faltantes

### Problema: Testes falhando

**Solução**: Verifique se todas as dependências foram instaladas corretamente e se as variáveis de ambiente estão configuradas corretamente

## Observações

- O backend do Suna requer Python 3.11 ou superior
- O ambiente virtual é criado no diretório `backend/venv`
- As dependências são instaladas usando o gerenciador de pacotes uv
- As variáveis de ambiente são configuradas no arquivo `backend/.env`