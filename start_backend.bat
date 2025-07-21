@echo off
echo ===================================================
echo Iniciando o Backend Suna
echo ===================================================
echo.

if not exist backend\venv (
    echo Ambiente virtual nao encontrado. Por favor, execute setup_python_env.bat primeiro.
    exit /b 1
)

echo Ativando ambiente virtual...
call backend\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    exit /b 1
)

echo.
echo Iniciando o backend...
cd backend
uv run api.py
cd ..

echo.
echo ===================================================
echo Backend encerrado!
echo ===================================================
echo.
echo Desativando ambiente virtual...
deactivate

echo.
echo Pressione qualquer tecla para sair...
pause > nul