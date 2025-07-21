@echo off
echo ===================================================
echo Configuracao do Ambiente Python para o Backend Suna
echo ===================================================
echo.

echo [1/5] Verificando a versao do Python instalada...
python --version 2>NUL
if %errorlevel% neq 0 (
    echo Python nao encontrado. Por favor, instale Python 3.11+ do site oficial:
    echo https://www.python.org/downloads/
    echo.
    echo Apos a instalacao, execute este script novamente.
    exit /b 1
)

echo Verificando se Python 3.11+ esta instalado...
py -3.11 --version 2>NUL
if %errorlevel% equ 0 (
    echo Python 3.11+ encontrado. Usando esta versao.
    set PYTHON_CMD=py -3.11
) else (
    python -c "import sys; print('Python ' + '.'.join(map(str, sys.version_info[:3])) + ' detectado'); exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo.
    echo ATENCAO: A versao do Python instalada e inferior a 3.11
    echo O backend do Suna requer Python 3.11 ou superior.
    echo.
    echo Por favor, instale Python 3.11+ do site oficial:
    echo https://www.python.org/downloads/
    echo.
    echo Apos a instalacao, execute este script novamente.
    exit /b 1
)
)

echo.
echo [2/5] Verificando se o pip esta atualizado...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

echo.
echo [3/5] Criando ambiente virtual...
if exist backend\venv (
    echo Ambiente virtual ja existe. Deseja recria-lo? (S/N)
    set /p recreate=
    if /i "%recreate%"=="S" (
        echo Removendo ambiente virtual existente...
        rmdir /s /q backend\venv
        echo Criando novo ambiente virtual...
        cd backend
        %PYTHON_CMD% -m venv venv
        cd ..
    ) else (
        echo Mantendo ambiente virtual existente.
    )
) else (
    echo Criando ambiente virtual...
    cd backend
    %PYTHON_CMD% -m venv venv
    cd ..
)

echo.
echo [4/5] Ativando ambiente virtual e instalando dependencias...
call backend\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Falha ao ativar o ambiente virtual.
    exit /b 1
)

echo Instalando dependencias com pip...
cd backend
pip install -e .
if %errorlevel% neq 0 (
    echo Falha ao instalar dependencias.
    exit /b 1
)
cd ..

echo.
echo [5/5] Configurando variaveis de ambiente...
if not exist backend\.env (
    echo Criando arquivo .env a partir de .env.example...
    copy backend\.env.example backend\.env
    echo Arquivo .env criado. Por favor, edite-o para configurar suas variaveis de ambiente.
) else (
    echo Comparando .env com .env.example para identificar novas variaveis...
    echo As seguintes variaveis podem precisar ser adicionadas ao seu arquivo .env:
    echo.
    
    for /f "tokens=*" %%a in ('findstr /v /c:"#" backend\.env.example') do (
        for /f "tokens=1 delims==" %%b in ("%%a") do (
            findstr /c:"%%b=" backend\.env >NUL
            if %errorlevel% neq 0 (
                echo %%a
            )
        )
    )
)

echo.
echo ===================================================
echo Configuracao do ambiente concluida com sucesso!
echo ===================================================
echo.
echo Para ativar o ambiente virtual:
echo   call backend\venv\Scripts\activate.bat
echo.
echo Para executar o backend:
echo   cd backend
echo   python api.py
echo.
echo Para executar os testes:
echo   cd backend
echo   python -m pytest
echo.
echo Para desativar o ambiente virtual:
echo   deactivate
echo.
echo Pressione qualquer tecla para sair...
pause > nul