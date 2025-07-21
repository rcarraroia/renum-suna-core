@echo off
echo ===================================================
echo Configuracao Completa do Ambiente (Nao Interativa)
echo ===================================================
echo.

echo [1/5] Verificando Python 3.11...
py -3.11 --version
if %errorlevel% neq 0 (
    echo Python 3.11 nao encontrado. Por favor, instale Python 3.11+ do site oficial:
    echo https://www.python.org/downloads/
    exit /b 1
)

echo.
echo [2/5] Criando ambiente virtual com Python 3.11...
if exist backend\venv311 (
    echo Removendo ambiente virtual existente...
    rmdir /s /q backend\venv311
)
echo Criando novo ambiente virtual...
py -3.11 -m venv backend\venv311

echo.
echo [3/5] Configurando variaveis de ambiente...
if not exist backend\.env (
    echo Criando arquivo .env a partir de .env.example...
    copy backend\.env.example backend\.env
    echo Arquivo .env criado.
) else (
    echo Arquivo .env ja existe.
)

echo.
echo [4/5] Ativando ambiente virtual e instalando dependencias...
call backend\venv311\Scripts\activate.bat
echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [5/5] Instalando dependencias essenciais...
pip install fastapi uvicorn python-dotenv pydantic httpx redis dramatiq pika supabase

echo.
echo ===================================================
echo Configuracao concluida com sucesso!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend...
cd backend
python api.py