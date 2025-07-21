@echo off
echo ===================================================
echo Instalacao de Dependencias do Backend Suna
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
echo Instalando dependencias essenciais...
pip install fastapi uvicorn python-dotenv pydantic

echo.
echo Para instalar todas as dependencias (pode demorar muito):
echo   cd backend
echo   pip install -e .
echo.
echo Ou voce pode instalar dependencias especificas conforme necessario.
echo.
echo Pressione qualquer tecla para sair...
pause > nul