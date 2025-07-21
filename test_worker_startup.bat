@echo off
echo ===================================================
echo Testando Inicializacao do Worker
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando teste de inicialização do worker > logs\test_worker_startup.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\test_worker_startup.log
    exit /b 1
)

if not exist backend\run_agent_background.py (
    echo ERRO: Arquivo run_agent_background.py nao encontrado em backend\run_agent_background.py
    echo Por favor, verifique se o arquivo run_agent_background.py existe.
    echo [%date% %time%] ERRO: Arquivo run_agent_background.py não encontrado >> logs\test_worker_startup.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\test_worker_startup.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\test_worker_startup.log
    exit /b 1
)

echo.
echo Verificando dependencias criticas para o worker...
echo [%date% %time%] Verificando dependências críticas para o worker >> logs\test_worker_startup.log

set deps_ok=1
for %%d in (dramatiq redis pydantic mcp) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% neq 0 (
        echo ERRO: Dependencia %%d nao encontrada.
        echo [%date% %time%] ERRO: Dependência %%d não encontrada >> logs\test_worker_startup.log
        set deps_ok=0
    )
)

if %deps_ok% equ 0 (
    echo.
    echo ERRO: Dependencias criticas estao faltando.
    echo Execute install_main_dependencies.bat e install_mcp_deps.bat primeiro.
    echo [%date% %time%] ERRO: Dependências críticas estão faltando >> logs\test_worker_startup.log
    goto cleanup
)

echo.
echo Testando importacao de modulos do worker...
echo [%date% %time%] Testando importação de módulos do worker >> logs\test_worker_startup.log

cd backend

REM Testar importação do Dramatiq
echo Testando importacao do Dramatiq...
python -c "import dramatiq; print('Dramatiq importado com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Nao foi possivel importar Dramatiq
    echo [%date% %time%] FALHOU: Não foi possível importar Dramatiq >> ..\logs\test_worker_startup.log
    goto worker_cleanup
) else (
    echo [PASSOU] Dramatiq importado com sucesso
    echo [%date% %time%] PASSOU: Dramatiq importado com sucesso >> ..\logs\test_worker_startup.log
)

REM Testar se o arquivo run_agent_background.py pode ser importado
echo Testando se run_agent_background.py pode ser importado...
python -c "import sys; sys.path.append('.'); import run_agent_background; print('Modulo run_agent_background importado com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Nao foi possivel importar o modulo run_agent_background
    echo [%date% %time%] FALHOU: Não foi possível importar o módulo run_agent_background >> ..\logs\test_worker_startup.log
    echo.
    echo Tentando identificar o problema...
    python -c "import sys; sys.path.append('.'); import run_agent_background" 2>&1 | findstr /C:"Error" /C:"Exception" /C:"Traceback"
    goto worker_cleanup
) else (
    echo [PASSOU] Modulo run_agent_background importado com sucesso
    echo [%date% %time%] PASSOU: Módulo run_agent_background importado com sucesso >> ..\logs\test_worker_startup.log
)

echo.
echo Verificando se o RabbitMQ esta disponivel...
echo [%date% %time%] Verificando se o RabbitMQ está disponível >> ..\logs\test_worker_startup.log

docker ps | findstr rabbitmq > nul
if %errorlevel% neq 0 (
    echo [AVISO] RabbitMQ nao parece estar em execucao
    echo [%date% %time%] AVISO: RabbitMQ não parece estar em execução >> ..\logs\test_worker_startup.log
    echo.
    echo Tentando iniciar o RabbitMQ...
    docker compose up rabbitmq -d > nul 2>&1
    if %errorlevel% neq 0 (
        echo [AVISO] Nao foi possivel iniciar o RabbitMQ automaticamente
        echo [%date% %time%] AVISO: Não foi possível iniciar o RabbitMQ automaticamente >> ..\logs\test_worker_startup.log
        echo O teste do worker pode falhar sem o RabbitMQ
    ) else (
        echo [INFO] RabbitMQ iniciado com sucesso
        echo [%date% %time%] INFO: RabbitMQ iniciado com sucesso >> ..\logs\test_worker_startup.log
        echo Aguardando 10 segundos para o RabbitMQ inicializar...
        timeout /t 10 /nobreak > nul
    )
) else (
    echo [PASSOU] RabbitMQ esta em execucao
    echo [%date% %time%] PASSOU: RabbitMQ está em execução >> ..\logs\test_worker_startup.log
)

echo.
echo Testando configuracao do broker Dramatiq...
echo [%date% %time%] Testando configuração do broker Dramatiq >> ..\logs\test_worker_startup.log

REM Criar um script temporário para testar a configuração do broker
echo import sys > test_worker_temp.py
echo sys.path.append('.') >> test_worker_temp.py
echo try: >> test_worker_temp.py
echo     import dramatiq >> test_worker_temp.py
echo     from dramatiq.brokers.rabbitmq import RabbitMQBroker >> test_worker_temp.py
echo     broker = RabbitMQBroker(host='localhost', port=5672) >> test_worker_temp.py
echo     print('Broker Dramatiq configurado com sucesso') >> test_worker_temp.py
echo     exit(0) >> test_worker_temp.py
echo except Exception as e: >> test_worker_temp.py
echo     print(f'Erro ao configurar broker: {e}') >> test_worker_temp.py
echo     exit(1) >> test_worker_temp.py

python test_worker_temp.py
set broker_test_result=%errorlevel%

REM Remover arquivo temporário
del test_worker_temp.py

if %broker_test_result% neq 0 (
    echo [FALHOU] Broker Dramatiq nao pode ser configurado
    echo [%date% %time%] FALHOU: Broker Dramatiq não pode ser configurado >> ..\logs\test_worker_startup.log
) else (
    echo [PASSOU] Broker Dramatiq configurado com sucesso
    echo [%date% %time%] PASSOU: Broker Dramatiq configurado com sucesso >> ..\logs\test_worker_startup.log
)

echo.
echo Testando inicializacao rapida do worker (10 segundos)...
echo [%date% %time%] Testando inicialização rápida do worker >> ..\logs\test_worker_startup.log

REM Iniciar o worker em background por 10 segundos
echo Iniciando worker em background...
start /B python -m dramatiq run_agent_background > worker_test_output.log 2>&1

REM Aguardar 5 segundos para o worker inicializar
echo Aguardando 5 segundos para o worker inicializar...
timeout /t 5 /nobreak > nul

REM Verificar se o processo está rodando
tasklist | findstr python > nul
if %errorlevel% equ 0 (
    echo [PASSOU] Worker parece estar executando
    echo [%date% %time%] PASSOU: Worker parece estar executando >> ..\logs\test_worker_startup.log
) else (
    echo [AVISO] Worker pode nao estar executando
    echo [%date% %time%] AVISO: Worker pode não estar executando >> ..\logs\test_worker_startup.log
)

REM Aguardar mais 5 segundos
timeout /t 5 /nobreak > nul

REM Tentar encerrar o processo do worker
echo Encerrando processo do worker...
taskkill /F /IM python.exe > nul 2>&1

REM Verificar se há saída de erro no log
if exist worker_test_output.log (
    findstr /C:"Error" /C:"Exception" /C:"Traceback" worker_test_output.log > nul
    if %errorlevel% equ 0 (
        echo [AVISO] Foram encontrados erros na saida do worker:
        echo [%date% %time%] AVISO: Foram encontrados erros na saída do worker >> ..\logs\test_worker_startup.log
        type worker_test_output.log
        type worker_test_output.log >> ..\logs\test_worker_startup.log
    ) else (
        echo [PASSOU] Worker executou sem erros criticos
        echo [%date% %time%] PASSOU: Worker executou sem erros críticos >> ..\logs\test_worker_startup.log
    )
    del worker_test_output.log
)

:worker_cleanup
cd ..

echo.
echo ===================================================
echo Resumo do teste de inicializacao do worker:
echo ===================================================
echo [%date% %time%] Resumo do teste de inicialização do worker >> logs\test_worker_startup.log

echo [INFO] Teste de inicializacao do worker concluido.
echo [%date% %time%] INFO: Teste de inicialização do worker concluído >> logs\test_worker_startup.log
echo.
echo Se houver problemas:
echo - Verifique os logs em logs\test_worker_startup.log
echo - Execute install_main_dependencies.bat para instalar dependencias
echo - Execute install_mcp_deps.bat para instalar MCP
echo - Certifique-se de que o RabbitMQ esta em execucao: docker compose up rabbitmq -d
echo - Verifique se o arquivo backend\.env existe e esta configurado
echo - Execute check_environment.bat para verificacao completa

:cleanup
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\test_worker_startup.log

echo.
echo ===================================================
echo Teste de inicializacao do worker concluido!
echo ===================================================
echo [%date% %time%] Teste de inicialização do worker concluído >> logs\test_worker_startup.log