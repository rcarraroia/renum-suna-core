@echo off
echo ===== Aplicando Esquema de Compartilhamento de Agentes no Supabase =====

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Erro: Python não encontrado. Por favor, instale o Python 3.6 ou superior.
    exit /b 1
)

REM Verificar se as dependências estão instaladas
pip show python-dotenv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Instalando dependências...
    pip install python-dotenv supabase httpx
)

REM Definir caminho para o arquivo SQL
set SQL_FILE=scripts\create_agent_share_table.sql

REM Verificar se o arquivo SQL existe
if not exist "%SQL_FILE%" (
    echo Erro: Arquivo SQL não encontrado: %SQL_FILE%
    exit /b 1
)

REM Verificar se o arquivo .env existe
if not exist ".env" (
    echo Arquivo .env não encontrado. Por favor, crie um arquivo .env com as credenciais do Supabase:
    echo SUPABASE_URL=https://seu-projeto.supabase.co
    echo SUPABASE_SERVICE_KEY=sua-chave-de-servico
    exit /b 1
)

REM Executar o script Python
echo Executando script Python...
python scripts\apply_supabase_schema.py %SQL_FILE%

if %ERRORLEVEL% neq 0 (
    echo Erro ao aplicar o esquema. Verifique os logs acima.
    exit /b 1
)

echo ===== Esquema aplicado com sucesso! =====