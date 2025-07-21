@echo off
echo ===================================================
echo Instalacao de Dependencias Comuns do Backend Suna
echo ===================================================
echo.

echo Ativando ambiente virtual...
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    echo Certifique-se de executar setup_env_simple.bat primeiro.
    exit /b 1
)

echo.
echo Instalando dependencias comuns...
pip install redis pika dramatiq supabase litellm httpx aiohttp cryptography pyjwt boto3 openai

echo.
echo Dependencias comuns instaladas com sucesso!
echo.
echo Para instalar todas as dependencias (pode demorar muito):
echo   pip install -e .
echo.
echo Pressione qualquer tecla para sair...
pause > nul