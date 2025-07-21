@echo off
echo ===================================================
echo Testando Instalacao de Dependencias
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando teste de instalação de dependências > logs\test_dependencies.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\test_dependencies.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\test_dependencies.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\test_dependencies.log
    exit /b 1
)

echo.
echo Verificando versao do Python...
echo [%date% %time%] Verificando versão do Python >> logs\test_dependencies.log
python --version
python --version >> logs\test_dependencies.log

echo.
echo ===================================================
echo Testando dependencias principais...
echo ===================================================
echo [%date% %time%] Testando dependências principais >> logs\test_dependencies.log

set test_passed=1

REM Testar FastAPI
echo Testando FastAPI...
python -c "import fastapi; print('FastAPI versao:', fastapi.__version__)" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] FastAPI nao pode ser importado
    echo [%date% %time%] FALHOU: FastAPI não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import fastapi; print('FastAPI versao:', fastapi.__version__)"
    python -c "import fastapi; print('FastAPI versao:', fastapi.__version__)" >> logs\test_dependencies.log
    echo [PASSOU] FastAPI importado com sucesso
    echo [%date% %time%] PASSOU: FastAPI importado com sucesso >> logs\test_dependencies.log
)

REM Testar Uvicorn
echo Testando Uvicorn...
python -c "import uvicorn; print('Uvicorn versao:', uvicorn.__version__)" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Uvicorn nao pode ser importado
    echo [%date% %time%] FALHOU: Uvicorn não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import uvicorn; print('Uvicorn versao:', uvicorn.__version__)"
    python -c "import uvicorn; print('Uvicorn versao:', uvicorn.__version__)" >> logs\test_dependencies.log
    echo [PASSOU] Uvicorn importado com sucesso
    echo [%date% %time%] PASSOU: Uvicorn importado com sucesso >> logs\test_dependencies.log
)

REM Testar Pydantic
echo Testando Pydantic...
python -c "import pydantic; print('Pydantic versao:', pydantic.VERSION)" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Pydantic nao pode ser importado
    echo [%date% %time%] FALHOU: Pydantic não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import pydantic; print('Pydantic versao:', pydantic.VERSION)"
    python -c "import pydantic; print('Pydantic versao:', pydantic.VERSION)" >> logs\test_dependencies.log
    echo [PASSOU] Pydantic importado com sucesso
    echo [%date% %time%] PASSOU: Pydantic importado com sucesso >> logs\test_dependencies.log
)

REM Testar MCP
echo Testando MCP...
python -c "import mcp; print('MCP importado com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] MCP nao pode ser importado
    echo [%date% %time%] FALHOU: MCP não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import mcp; print('MCP importado com sucesso')"
    python -c "import mcp; print('MCP importado com sucesso')" >> logs\test_dependencies.log
    echo [PASSOU] MCP importado com sucesso
    echo [%date% %time%] PASSOU: MCP importado com sucesso >> logs\test_dependencies.log
)

REM Testar Redis
echo Testando Redis...
python -c "import redis; print('Redis versao:', redis.__version__)" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Redis nao pode ser importado
    echo [%date% %time%] FALHOU: Redis não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import redis; print('Redis versao:', redis.__version__)"
    python -c "import redis; print('Redis versao:', redis.__version__)" >> logs\test_dependencies.log
    echo [PASSOU] Redis importado com sucesso
    echo [%date% %time%] PASSOU: Redis importado com sucesso >> logs\test_dependencies.log
)

REM Testar Dramatiq
echo Testando Dramatiq...
python -c "import dramatiq; print('Dramatiq versao:', dramatiq.__version__)" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Dramatiq nao pode ser importado
    echo [%date% %time%] FALHOU: Dramatiq não pode ser importado >> logs\test_dependencies.log
    set test_passed=0
) else (
    python -c "import dramatiq; print('Dramatiq versao:', dramatiq.__version__)"
    python -c "import dramatiq; print('Dramatiq versao:', dramatiq.__version__)" >> logs\test_dependencies.log
    echo [PASSOU] Dramatiq importado com sucesso
    echo [%date% %time%] PASSOU: Dramatiq importado com sucesso >> logs\test_dependencies.log
)

echo.
echo ===================================================
echo Testando funcionalidades basicas...
echo ===================================================
echo [%date% %time%] Testando funcionalidades básicas >> logs\test_dependencies.log

REM Testar criação de aplicação FastAPI básica
echo Testando criacao de aplicacao FastAPI basica...
python -c "from fastapi import FastAPI; app = FastAPI(); print('Aplicacao FastAPI criada com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Nao foi possivel criar aplicacao FastAPI
    echo [%date% %time%] FALHOU: Não foi possível criar aplicação FastAPI >> logs\test_dependencies.log
    set test_passed=0
) else (
    echo [PASSOU] Aplicacao FastAPI criada com sucesso
    echo [%date% %time%] PASSOU: Aplicação FastAPI criada com sucesso >> logs\test_dependencies.log
)

REM Testar validação Pydantic
echo Testando validacao Pydantic...
python -c "from pydantic import BaseModel; class Test(BaseModel): name: str; t = Test(name='test'); print('Validacao Pydantic funcionando')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Validacao Pydantic nao esta funcionando
    echo [%date% %time%] FALHOU: Validação Pydantic não está funcionando >> logs\test_dependencies.log
    set test_passed=0
) else (
    echo [PASSOU] Validacao Pydantic funcionando
    echo [%date% %time%] PASSOU: Validação Pydantic funcionando >> logs\test_dependencies.log
)

echo.
echo ===================================================
echo Resumo dos testes:
echo ===================================================
echo [%date% %time%] Resumo dos testes >> logs\test_dependencies.log

if %test_passed% equ 1 (
    echo [SUCESSO] Todos os testes passaram!
    echo [%date% %time%] SUCESSO: Todos os testes passaram >> logs\test_dependencies.log
    echo.
    echo As dependencias estao instaladas e funcionando corretamente.
    echo [%date% %time%] As dependências estão instaladas e funcionando corretamente >> logs\test_dependencies.log
) else (
    echo [FALHA] Alguns testes falharam!
    echo [%date% %time%] FALHA: Alguns testes falharam >> logs\test_dependencies.log
    echo.
    echo Verifique os logs em logs\test_dependencies.log para mais detalhes.
    echo [%date% %time%] Verifique os logs para mais detalhes >> logs\test_dependencies.log
    echo.
    echo Recomendacoes:
    echo - Execute install_main_dependencies.bat para instalar dependencias principais
    echo - Execute install_mcp_deps.bat para instalar MCP e dependencias relacionadas
    echo - Execute check_missing_dependencies.bat para verificar dependencias faltantes
)

echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\test_dependencies.log

echo.
echo ===================================================
echo Teste de instalacao de dependencias concluido!
echo ===================================================
echo [%date% %time%] Teste de instalação de dependências concluído >> logs\test_dependencies.log