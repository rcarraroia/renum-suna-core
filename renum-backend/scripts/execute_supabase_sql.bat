@echo off
echo ===== Executando SQL no Supabase =====

REM Verificar se o arquivo SQL foi especificado
if "%~1"=="" (
    echo Erro: Arquivo SQL não especificado.
    echo Uso: execute_supabase_sql.bat [arquivo_sql]
    exit /b 1
)

REM Verificar se o arquivo SQL existe
if not exist "%~1" (
    echo Erro: Arquivo SQL não encontrado: %~1
    exit /b 1
)

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Erro: Python não encontrado. Por favor, instale o Python 3.6 ou superior.
    exit /b 1
)

REM Verificar se as dependências estão instaladas
pip show supabase-py >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Instalando dependências...
    pip install supabase-py python-dotenv
)

REM Solicitar credenciais do Supabase se não estiverem no .env
set ENV_FILE=../.env
if not exist %ENV_FILE% (
    echo Arquivo .env não encontrado. Por favor, forneça as credenciais do Supabase:
    set /p SUPABASE_URL="URL do Supabase: "
    set /p SUPABASE_SERVICE_KEY="Chave de serviço do Supabase: "
    
    REM Criar arquivo .env temporário
    echo SUPABASE_URL=%SUPABASE_URL%> temp.env
    echo SUPABASE_SERVICE_KEY=%SUPABASE_SERVICE_KEY%>> temp.env
    set ENV_FILE=temp.env
)

REM Executar o script Python
echo Executando script Python...
python execute_supabase_sql.py --file "%~1" --env %ENV_FILE%

REM Remover arquivo .env temporário se foi criado
if exist temp.env del temp.env

echo ===== Concluído =====