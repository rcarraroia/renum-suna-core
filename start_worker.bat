@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Iniciando o Worker do Backend Suna
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando o worker > logs\start_worker.log

REM Verificar se o diretório backend existe
if not exist backend (
    echo ERRO: Diretorio backend nao encontrado.
    echo Por favor, verifique se o diretorio backend existe.
    echo [%date% %time%] ERRO: Diretório backend não encontrado >> logs\start_worker.log
    goto error
)

REM Verificar se o ambiente virtual existe
if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\start_worker.log
    goto error
)

REM Verificar se o arquivo run_agent_background.py existe
if not exist backend\run_agent_background.py (
    echo ERRO: Arquivo run_agent_background.py nao encontrado em backend\run_agent_background.py
    echo Por favor, verifique se o arquivo run_agent_background.py existe.
    echo [%date% %time%] ERRO: Arquivo run_agent_background.py não encontrado >> logs\start_worker.log
    goto error
)

REM Verificar se o arquivo .env existe
if not exist backend\.env (
    echo AVISO: Arquivo .env nao encontrado em backend\.env
    echo O worker pode nao funcionar corretamente sem as variaveis de ambiente.
    echo [%date% %time%] AVISO: Arquivo .env não encontrado >> logs\start_worker.log
    
    echo Deseja continuar mesmo assim? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo Inicializacao cancelada pelo usuario.
        echo [%date% %time%] Inicialização cancelada pelo usuário >> logs\start_worker.log
        goto error
    )
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\start_worker.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\start_worker.log
    goto error
)

REM Verificar versão do Python
echo Verificando versao do Python...
echo [%date% %time%] Verificando versão do Python >> logs\start_worker.log
python --version | findstr "3.11" > nul
if %errorlevel% neq 0 (
    echo AVISO: A versao do Python pode nao ser 3.11. Isso pode causar problemas.
    echo Versao atual:
    python --version
    python --version >> logs\start_worker.log
    
    echo Deseja continuar mesmo assim? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo Inicializacao cancelada pelo usuario.
        echo [%date% %time%] Inicialização cancelada pelo usuário >> logs\start_worker.log
        goto cleanup
    )
)

REM Verificar dependências críticas
echo Verificando dependencias criticas...
echo [%date% %time%] Verificando dependências críticas >> logs\start_worker.log
set deps_ok=1

REM Lista de dependências críticas para verificar
for %%d in (dramatiq redis pydantic mcp) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% neq 0 (
        echo AVISO: Dependencia %%d nao encontrada.
        echo [%date% %time%] AVISO: Dependência %%d não encontrada >> logs\start_worker.log
        set deps_ok=0
    )
)

if !deps_ok! equ 0 (
    echo.
    echo AVISO: Algumas dependencias criticas estao faltando.
    echo Deseja instalar as dependencias faltantes agora? (S/N)
    set /p instalar=
    if /i "%instalar%"=="S" (
        echo Instalando dependencias...
        echo [%date% %time%] Instalando dependências >> logs\start_worker.log
        call install_mcp_deps.bat
        if %errorlevel% neq 0 (
            echo ERRO: Falha ao instalar dependencias.
            echo [%date% %time%] ERRO: Falha ao instalar dependências >> logs\start_worker.log
            goto cleanup
        )
    ) else (
        echo Continuando sem instalar dependencias...
        echo [%date% %time%] Continuando sem instalar dependências >> logs\start_worker.log
    )
)

REM Verificar se o RabbitMQ está em execução
echo Verificando se o RabbitMQ esta em execucao...
echo [%date% %time%] Verificando se o RabbitMQ está em execução >> logs\start_worker.log
docker ps | findstr rabbitmq > nul
if %errorlevel% neq 0 (
    echo AVISO: O RabbitMQ parece nao estar em execucao.
    echo O worker pode nao funcionar corretamente sem o RabbitMQ.
    echo [%date% %time%] AVISO: RabbitMQ não está em execução >> logs\start_worker.log
    
    echo Deseja iniciar o RabbitMQ agora? (S/N)
    set /p iniciar_rabbitmq=
    if /i "%iniciar_rabbitmq%"=="S" (
        echo Iniciando o RabbitMQ...
        echo [%date% %time%] Iniciando o RabbitMQ >> logs\start_worker.log
        docker compose up rabbitmq -d
        if %errorlevel% neq 0 (
            echo ERRO: Falha ao iniciar o RabbitMQ.
            echo [%date% %time%] ERRO: Falha ao iniciar o RabbitMQ >> logs\start_worker.log
        ) else (
            echo RabbitMQ iniciado com sucesso.
            echo [%date% %time%] RabbitMQ iniciado com sucesso >> logs\start_worker.log
            echo Aguardando 10 segundos para o RabbitMQ inicializar...
            timeout /t 10 /nobreak > nul
        )
    ) else (
        echo Continuando sem iniciar o RabbitMQ...
        echo [%date% %time%] Continuando sem iniciar o RabbitMQ >> logs\start_worker.log
    )
)

echo.
echo Iniciando o worker...
echo [%date% %time%] Iniciando o worker >> logs\start_worker.log
cd backend
python -m dramatiq run_agent_background
set worker_exit_code=%errorlevel%
cd ..

if %worker_exit_code% neq 0 (
    echo.
    echo AVISO: O worker foi encerrado com codigo de saida %worker_exit_code%.
    echo [%date% %time%] AVISO: Worker encerrado com código de saída %worker_exit_code% >> logs\start_worker.log
) else (
    echo.
    echo ===================================================
    echo Worker encerrado normalmente!
    echo ===================================================
    echo [%date% %time%] Worker encerrado normalmente >> logs\start_worker.log
)

:cleanup
echo.
echo Desativando ambiente virtual...
echo [%date% %time%] Desativando ambiente virtual >> logs\start_worker.log
deactivate

goto end

:error
echo.
echo ===================================================
echo Falha ao iniciar o worker!
echo ===================================================
echo [%date% %time%] Falha ao iniciar o worker >> logs\start_worker.log

:end
echo.
echo Pressione qualquer tecla para sair...
pause > nul