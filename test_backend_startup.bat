@echo off
echo ===================================================
echo Testando Inicializacao do Backend
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando teste de inicialização do backend > logs\test_backend_startup.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\test_backend_startup.log
    exit /b 1
)

if not exist backend\api.py (
    echo ERRO: Arquivo api.py nao encontrado em backend\api.py
    echo Por favor, verifique se o arquivo api.py existe.
    echo [%date% %time%] ERRO: Arquivo api.py não encontrado >> logs\test_backend_startup.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\test_backend_startup.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\test_backend_startup.log
    exit /b 1
)

echo.
echo Verificando dependencias criticas...
echo [%date% %time%] Verificando dependências críticas >> logs\test_backend_startup.log

set deps_ok=1
for %%d in (fastapi uvicorn pydantic mcp) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% neq 0 (
        echo ERRO: Dependencia %%d nao encontrada.
        echo [%date% %time%] ERRO: Dependência %%d não encontrada >> logs\test_backend_startup.log
        set deps_ok=0
    )
)

if %deps_ok% equ 0 (
    echo.
    echo ERRO: Dependencias criticas estao faltando.
    echo Execute install_main_dependencies.bat e install_mcp_deps.bat primeiro.
    echo [%date% %time%] ERRO: Dependências críticas estão faltando >> logs\test_backend_startup.log
    goto cleanup
)

echo.
echo Testando importacao de modulos do backend...
echo [%date% %time%] Testando importação de módulos do backend >> logs\test_backend_startup.log

cd backend

REM Testar importação básica do FastAPI
echo Testando importacao do FastAPI...
python -c "from fastapi import FastAPI; print('FastAPI importado com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Nao foi possivel importar FastAPI
    echo [%date% %time%] FALHOU: Não foi possível importar FastAPI >> ..\logs\test_backend_startup.log
    goto backend_cleanup
) else (
    echo [PASSOU] FastAPI importado com sucesso
    echo [%date% %time%] PASSOU: FastAPI importado com sucesso >> ..\logs\test_backend_startup.log
)

REM Testar se o arquivo api.py pode ser importado
echo Testando se api.py pode ser importado...
python -c "import sys; sys.path.append('.'); import api; print('Modulo api importado com sucesso')" > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALHOU] Nao foi possivel importar o modulo api
    echo [%date% %time%] FALHOU: Não foi possível importar o módulo api >> ..\logs\test_backend_startup.log
    echo.
    echo Tentando identificar o problema...
    python -c "import sys; sys.path.append('.'); import api" 2>&1 | findstr /C:"Error" /C:"Exception" /C:"Traceback"
    goto backend_cleanup
) else (
    echo [PASSOU] Modulo api importado com sucesso
    echo [%date% %time%] PASSOU: Módulo api importado com sucesso >> ..\logs\test_backend_startup.log
)

echo.
echo Testando inicializacao rapida do backend (5 segundos)...
echo [%date% %time%] Testando inicialização rápida do backend >> ..\logs\test_backend_startup.log

REM Criar um script temporário para testar o backend
echo import sys > test_backend_temp.py
echo sys.path.append('.') >> test_backend_temp.py
echo try: >> test_backend_temp.py
echo     import api >> test_backend_temp.py
echo     print('Backend pode ser inicializado') >> test_backend_temp.py
echo     exit(0) >> test_backend_temp.py
echo except Exception as e: >> test_backend_temp.py
echo     print(f'Erro ao inicializar backend: {e}') >> test_backend_temp.py
echo     exit(1) >> test_backend_temp.py

python test_backend_temp.py
set backend_test_result=%errorlevel%

REM Remover arquivo temporário
del test_backend_temp.py

if %backend_test_result% neq 0 (
    echo [FALHOU] Backend nao pode ser inicializado
    echo [%date% %time%] FALHOU: Backend não pode ser inicializado >> ..\logs\test_backend_startup.log
    goto backend_cleanup
) else (
    echo [PASSOU] Backend pode ser inicializado
    echo [%date% %time%] PASSOU: Backend pode ser inicializado >> ..\logs\test_backend_startup.log
)

echo.
echo Testando se o backend responde (teste de 10 segundos)...
echo [%date% %time%] Testando se o backend responde >> ..\logs\test_backend_startup.log

REM Iniciar o backend em background por 10 segundos
echo Iniciando backend em background...
start /B python api.py > backend_test_output.log 2>&1
set backend_pid=%!

REM Aguardar 5 segundos para o backend inicializar
echo Aguardando 5 segundos para o backend inicializar...
timeout /t 5 /nobreak > nul

REM Tentar fazer uma requisição HTTP simples (se curl estiver disponível)
curl --version > nul 2>&1
if %errorlevel% equ 0 (
    echo Testando requisicao HTTP...
    curl -s http://localhost:8000/docs > nul 2>&1
    if %errorlevel% equ 0 (
        echo [PASSOU] Backend esta respondendo a requisicoes HTTP
        echo [%date% %time%] PASSOU: Backend está respondendo a requisições HTTP >> ..\logs\test_backend_startup.log
    ) else (
        echo [AVISO] Backend pode nao estar respondendo na porta 8000
        echo [%date% %time%] AVISO: Backend pode não estar respondendo na porta 8000 >> ..\logs\test_backend_startup.log
    )
) else (
    echo [INFO] curl nao disponivel, pulando teste de requisicao HTTP
    echo [%date% %time%] INFO: curl não disponível, pulando teste de requisição HTTP >> ..\logs\test_backend_startup.log
)

REM Aguardar mais 5 segundos
timeout /t 5 /nobreak > nul

REM Tentar encerrar o processo do backend
echo Encerrando processo do backend...
taskkill /F /IM python.exe > nul 2>&1

REM Verificar se há saída de erro no log
if exist backend_test_output.log (
    findstr /C:"Error" /C:"Exception" /C:"Traceback" backend_test_output.log > nul
    if %errorlevel% equ 0 (
        echo [AVISO] Foram encontrados erros na saida do backend:
        echo [%date% %time%] AVISO: Foram encontrados erros na saída do backend >> ..\logs\test_backend_startup.log
        type backend_test_output.log
        type backend_test_output.log >> ..\logs\test_backend_startup.log
    ) else (
        echo [PASSOU] Backend executou sem erros criticos
        echo [%date% %time%] PASSOU: Backend executou sem erros críticos >> ..\logs\test_backend_startup.log
    )
    del backend_test_output.log
)

:backend_cleanup
cd ..

echo.
echo ===================================================
echo Resumo do teste de inicializacao do backend:
echo ===================================================
echo [%date% %time%] Resumo do teste de inicialização do backend >> logs\test_backend_startup.log

echo [INFO] Teste de inicializacao do backend concluido.
echo [%date% %time%] INFO: Teste de inicialização do backend concluído >> logs\test_backend_startup.log
echo.
echo Se houver problemas:
echo - Verifique os logs em logs\test_backend_startup.log
echo - Execute install_main_dependencies.bat para instalar dependencias
echo - Execute install_mcp_deps.bat para instalar MCP
echo - Verifique se o arquivo backend\.env existe e esta configurado
echo - Execute check_environment.bat para verificacao completa

:cleanup
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\test_backend_startup.log

echo.
echo ===================================================
echo Teste de inicializacao do backend concluido!
echo ===================================================
echo [%date% %time%] Teste de inicialização do backend concluído >> logs\test_backend_startup.log