@echo off
echo ===================================================
echo Execucao de Testes do Backend Suna
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
echo Executando testes...
cd backend
python -m pytest -xvs
cd ..

echo.
echo ===================================================
echo Execucao de testes concluida!
echo ===================================================
echo.
echo Desativando ambiente virtual...
deactivate

echo.
echo Pressione qualquer tecla para sair...
pause > nul