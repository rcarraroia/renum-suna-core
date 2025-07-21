@echo off
echo ===================================================
echo Configuracao Simplificada do Ambiente Python
echo ===================================================
echo.

echo [1/4] Verificando Python 3.11...
py -3.11 --version
if %errorlevel% neq 0 (
    echo Python 3.11 nao encontrado. Por favor, instale Python 3.11+ do site oficial:
    echo https://www.python.org/downloads/
    exit /b 1
)

echo.
echo [2/4] Criando ambiente virtual com Python 3.11...
if exist backend\venv311 (
    echo Ambiente virtual ja existe. Deseja recria-lo? (S/N)
    set /p recreate=
    if /i "%recreate%"=="S" (
        echo Removendo ambiente virtual existente...
        rmdir /s /q backend\venv311
        echo Criando novo ambiente virtual...
        py -3.11 -m venv backend\venv311
    ) else (
        echo Mantendo ambiente virtual existente.
    )
) else (
    echo Criando ambiente virtual...
    py -3.11 -m venv backend\venv311
)

echo.
echo [3/4] Configurando variaveis de ambiente...
if not exist backend\.env (
    echo Criando arquivo .env a partir de .env.example...
    copy backend\.env.example backend\.env
    echo Arquivo .env criado. Por favor, edite-o para configurar suas variaveis de ambiente.
) else (
    echo Arquivo .env ja existe.
)

echo.
echo [4/4] Instalando dependencias essenciais...
echo Este processo pode demorar alguns minutos.
call backend\venv311\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo ===================================================
echo Configuracao basica concluida com sucesso!
echo ===================================================
echo.
echo Para ativar o ambiente virtual:
echo   call backend\venv311\Scripts\activate.bat
echo.
echo Para instalar todas as dependencias (pode demorar):
echo   cd backend
echo   pip install -e .
echo.
echo Para executar o backend:
echo   cd backend
echo   python api.py
echo.
echo Para desativar o ambiente virtual:
echo   deactivate
echo.
echo Pressione qualquer tecla para sair...
pause > nul