@echo off
echo ===== Verificando Integracao Renum-Suna =====

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Erro: Python não encontrado. Por favor, instale o Python 3.6 ou superior.
    exit /b 1
)

REM Verificar se as dependências estão instaladas
pip show supabase python-dotenv requests tabulate >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependências...
    pip install supabase python-dotenv requests tabulate
)

REM Verificar se o arquivo .env existe
if not exist ".env" (
    echo Erro: Arquivo .env não encontrado.
    exit /b 1
)

REM Executar o script Python
echo Executando verificação de integração...
python scripts\verify_integration.py

if %ERRORLEVEL% NEQ 0 (
    echo Erro ao verificar integração. Verifique os logs acima.
    exit /b 1
)

echo ===== Verificação concluída! =====