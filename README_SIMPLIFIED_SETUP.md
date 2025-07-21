# Configuração Simplificada do Ambiente

Devido à complexidade do backend do Suna e ao grande número de dependências, criamos uma abordagem simplificada para configurar o ambiente.

## Passos para Configuração

### 1. Configuração Básica

Execute o script `setup_env_simple.bat` para:
- Verificar se Python 3.11+ está instalado
- Criar um ambiente virtual com Python 3.11
- Configurar o arquivo `.env`
- Atualizar pip

```
setup_env_simple.bat
```

### 2. Instalação de Dependências

Você tem duas opções para instalar as dependências:

#### Opção 1: Instalar apenas dependências essenciais

Execute o script `install_dependencies.bat` para instalar apenas as dependências essenciais:
- fastapi
- uvicorn
- python-dotenv
- pydantic

```
install_dependencies.bat
```

#### Opção 2: Instalar todas as dependências

Para instalar todas as dependências (pode demorar muito):

```
call backend\venv311\Scripts\activate.bat
cd backend
pip install -e .
```

### 3. Instalação Incremental de Dependências

Se você encontrar erros ao executar o backend, você pode instalar dependências adicionais conforme necessário:

```
call backend\venv311\Scripts\activate.bat
pip install nome-da-dependencia
```

## Execução do Backend

Para executar o backend:

```
call backend\venv311\Scripts\activate.bat
cd backend
python api.py
```

## Execução do Worker

Para executar o worker:

```
call backend\venv311\Scripts\activate.bat
cd backend
python -m dramatiq run_agent_background
```

## Observações

- O backend do Suna requer Python 3.11 ou superior
- O ambiente virtual é criado no diretório `backend/venv311`
- As dependências são instaladas usando pip
- As variáveis de ambiente são configuradas no arquivo `backend/.env`