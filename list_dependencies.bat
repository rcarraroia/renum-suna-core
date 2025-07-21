@echo off
echo ===================================================
echo Listando Dependencias Instaladas
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Listando dependências instaladas > logs\list_dependencies.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\list_dependencies.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\list_dependencies.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\list_dependencies.log
    exit /b 1
)

echo.
echo Versao do Python:
python --version
python --version >> logs\list_dependencies.log

echo.
echo ===================================================
echo Todas as dependencias instaladas:
echo ===================================================
echo [%date% %time%] Listando todas as dependências >> logs\list_dependencies.log

REM Criar arquivo temporário para a lista de dependências
pip list > temp_deps.txt
type temp_deps.txt
type temp_deps.txt >> logs\list_dependencies.log

echo.
echo ===================================================
echo Dependencias principais do projeto:
echo ===================================================
echo [%date% %time%] Verificando dependências principais >> logs\list_dependencies.log

REM Lista de dependências principais para verificar
set deps=mcp fastapi uvicorn pydantic aiohttp websockets dramatiq redis supabase

for %%d in (%deps%) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% equ 0 (
        echo [INSTALADO] %%d
        pip show %%d | findstr "Version"
        echo [INSTALADO] %%d >> logs\list_dependencies.log
        pip show %%d | findstr "Version" >> logs\list_dependencies.log
    ) else (
        echo [NAO INSTALADO] %%d
        echo [NAO INSTALADO] %%d >> logs\list_dependencies.log
    )
)

echo.
echo ===================================================
echo Exportando lista completa para requirements_atual.txt
echo ===================================================
echo [%date% %time%] Exportando lista completa para requirements_atual.txt >> logs\list_dependencies.log

pip freeze > requirements_atual.txt
echo Lista exportada para requirements_atual.txt
echo [%date% %time%] Lista exportada para requirements_atual.txt >> logs\list_dependencies.log

REM Remover arquivo temporário
del temp_deps.txt

echo.
echo ===================================================
echo Listagem de dependencias concluida!
echo ===================================================
echo [%date% %time%] Listagem de dependências concluída >> logs\list_dependencies.log
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\list_dependencies.log