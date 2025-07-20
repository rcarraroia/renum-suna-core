@echo off
echo ===== Executando SQL diretamente no Supabase =====

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Erro: Python não encontrado. Por favor, instale o Python 3.6 ou superior.
    exit /b 1
)

REM Verificar se as dependências estão instaladas
pip show supabase >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Instalando dependências...
    pip install supabase python-dotenv
)

REM Verificar argumentos
if "%~1"=="" (
    echo Uso: execute_sql_direct.bat [arquivo_sql]
    exit /b 1
)

REM Verificar se o arquivo SQL existe
if not exist "%~1" (
    echo Erro: Arquivo SQL não encontrado: %~1
    exit /b 1
)

REM Verificar se o arquivo .env existe
if not exist ".env" (
    echo Erro: Arquivo .env não encontrado.
    exit /b 1
)

REM Executar o script Python
echo Executando script Python...
python scripts\execute_sql_direct.py "%~1"

if %ERRORLEVEL% neq 0 (
    echo Erro ao executar SQL. Verifique os logs acima.
    exit /b 1
)

echo ===== SQL executado com sucesso! =====