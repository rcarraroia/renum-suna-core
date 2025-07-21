@echo off
setlocal enabledelayedexpansion

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando gerenciamento do backend > logs\manage_backend.log

echo ===================================================
echo Gerenciamento do Backend Suna
echo ===================================================
echo.

:menu
cls
echo Escolha uma opcao:
echo.
echo === Instalacao e Verificacao ===
echo 1. Instalar dependencias principais
echo 2. Instalar dependencias faltantes (incluindo MCP)
echo 3. Instalar dependencias relacionadas ao MCP
echo 4. Listar todas as dependencias instaladas
echo 5. Verificar dependencias faltantes
echo 6. Verificar compatibilidade de versoes
echo.
echo === Execucao ===
echo 7. Iniciar o backend
echo 8. Iniciar o worker
echo.
echo === Testes ===
echo 9. Testar instalacao de dependencias
echo 10. Testar inicializacao do backend
echo 11. Testar inicializacao do worker
echo.
echo === Diagnostico ===
echo 12. Verificar ambiente Python
echo 13. Verificar variaveis de ambiente
echo 14. Verificar ambiente completo
echo 15. Executar testes
echo.
echo 16. Sair
echo.
set /p opcao="Digite o numero da opcao desejada: "

if "%opcao%"=="1" goto instalar_deps_principais
if "%opcao%"=="2" goto instalar_deps
if "%opcao%"=="3" goto instalar_deps_mcp
if "%opcao%"=="4" goto listar_deps
if "%opcao%"=="5" goto verificar_deps_faltantes
if "%opcao%"=="6" goto verificar_compatibilidade
if "%opcao%"=="7" goto iniciar_backend
if "%opcao%"=="8" goto iniciar_worker
if "%opcao%"=="9" goto testar_deps
if "%opcao%"=="10" goto testar_backend
if "%opcao%"=="11" goto testar_worker
if "%opcao%"=="12" goto verificar_python
if "%opcao%"=="13" goto verificar_env
if "%opcao%"=="14" goto verificar_ambiente_completo
if "%opcao%"=="15" goto executar_testes
if "%opcao%"=="16" goto sair
echo Opcao invalida. Tente novamente.
pause
goto menu

:instalar_deps
cls
echo ===================================================
echo Instalando Dependencias Faltantes
echo ===================================================
echo.
echo [%date% %time%] Iniciando instalação de dependências faltantes >> logs\manage_backend.log

REM Verificar ambiente
call error_handling.bat :check_environment logs\manage_backend.log
if %errorlevel% neq 0 (
    echo Por favor, corrija os problemas acima antes de continuar.
    echo [%date% %time%] Falha na verificação do ambiente >> logs\manage_backend.log
    pause
    goto menu
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\manage_backend.log
call backend\venv311\Scripts\activate.bat

echo Instalando mcp...
pip install mcp

echo Instalando outras dependencias que podem estar faltando...
pip install fastapi-cli uvicorn[standard] python-dotenv pydantic==1.10.8

echo Verificando dependencias do projeto...
cd backend
pip install -e .
cd ..

echo.
echo Instalacao concluida!
pause
goto menu

:iniciar_backend
cls
echo ===================================================
echo Iniciando o Backend Suna
echo ===================================================
echo.

if not exist backend\venv311 (
    echo Ambiente virtual Python 3.11 nao encontrado. Por favor, execute setup_complete_noninteractive.bat primeiro.
    pause
    goto menu
)

echo Ativando ambiente virtual Python 3.11...
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    pause
    goto menu
)

echo.
echo Iniciando o backend...
cd backend
python api.py
cd ..

echo.
echo Backend encerrado!
echo Desativando ambiente virtual...
deactivate
pause
goto menu

:iniciar_worker
cls
echo ===================================================
echo Iniciando o Worker do Backend Suna
echo ===================================================
echo.

if not exist backend\venv311 (
    echo Ambiente virtual Python 3.11 nao encontrado. Por favor, execute setup_complete_noninteractive.bat primeiro.
    pause
    goto menu
)

echo Ativando ambiente virtual Python 3.11...
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    pause
    goto menu
)

echo.
echo Iniciando o worker...
cd backend
python -m dramatiq run_agent_background
cd ..

echo.
echo Worker encerrado!
echo Desativando ambiente virtual...
deactivate
pause
goto menu

:verificar_python
cls
echo ===================================================
echo Verificando Ambiente Python
echo ===================================================
echo.

if not exist backend\venv311 (
    echo Ambiente virtual Python 3.11 nao encontrado. Por favor, execute setup_complete_noninteractive.bat primeiro.
    pause
    goto menu
)

echo Ativando ambiente virtual Python 3.11...
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    pause
    goto menu
)

echo.
echo Versao do Python:
python --version

echo.
echo Pacotes instalados:
pip list

echo.
echo Verificacao concluida!
echo Desativando ambiente virtual...
deactivate
pause
goto menu

:verificar_env
cls
echo ===================================================
echo Verificando Variaveis de Ambiente
echo ===================================================
echo.

if not exist backend\.env (
    echo Arquivo .env nao encontrado. Por favor, crie o arquivo backend\.env.
    pause
    goto menu
)

echo Variaveis de ambiente encontradas no arquivo backend\.env:
type backend\.env | findstr /v "^#" | findstr /v "^$"

echo.
echo Verificacao concluida!
pause
goto menu

:executar_testes
cls
echo ===================================================
echo Executando Testes
echo ===================================================
echo.

if not exist backend\venv311 (
    echo Ambiente virtual Python 3.11 nao encontrado. Por favor, execute setup_complete_noninteractive.bat primeiro.
    pause
    goto menu
)

echo Ativando ambiente virtual Python 3.11...
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    pause
    goto menu
)

echo.
echo Executando testes...
cd backend
python -m pytest
cd ..

echo.
echo Testes concluidos!
echo Desativando ambiente virtual...
deactivate
pause
goto menu

:sair
echo.
echo Saindo...
exit /b 0
:in
stalar_deps_mcp
cls
echo ===================================================
echo Instalando Dependencias Relacionadas ao MCP
echo ===================================================
echo.

call install_mcp_related_deps.bat
pause
goto menu

:listar_deps
cls
echo ===================================================
echo Listando Dependencias Instaladas
echo ===================================================
echo.

call list_dependencies.bat
pause
goto menu

:verificar_deps_faltantes
cls
echo ===================================================
echo Verificando Dependencias Faltantes
echo ===================================================
echo.

call check_missing_dependencies.bat
pause
goto menu

:verificar_compatibilidade
cls
echo ===================================================
echo Verificando Compatibilidade de Versoes
echo ===================================================
echo.

call check_version_compatibility.bat
pause
goto menu:verif
icar_ambiente_completo
cls
echo ===================================================
echo Verificando Ambiente Completo
echo ===================================================
echo.

call check_environment.bat
pause
goto menu:
instalar_deps_principais
cls
echo ===================================================
echo Instalando Dependencias Principais
echo ===================================================
echo.

call install_main_dependencies.bat
pause
goto menu

:testar_deps
cls
echo ===================================================
echo Testando Instalacao de Dependencias
echo ===================================================
echo.

call test_dependencies_installation.bat
pause
goto menu

:testar_backend
cls
echo ===================================================
echo Testando Inicializacao do Backend
echo ===================================================
echo.

call test_backend_startup.bat
pause
goto menu

:testar_worker
cls
echo ===================================================
echo Testando Inicializacao do Worker
echo ===================================================
echo.

call test_worker_startup.bat
pause
goto menu