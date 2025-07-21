@echo off
echo ===================================================
echo Verificando Dependencias Faltantes
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Verificando dependências faltantes > logs\check_missing_deps.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\check_missing_deps.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\check_missing_deps.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\check_missing_deps.log
    exit /b 1
)

echo.
echo Criando lista de dependências necessárias...
echo [%date% %time%] Criando lista de dependências necessárias >> logs\check_missing_deps.log

REM Lista de dependências necessárias para o projeto
echo mcp > required_deps.txt
echo fastapi >> required_deps.txt
echo uvicorn >> required_deps.txt
echo pydantic >> required_deps.txt
echo dramatiq >> required_deps.txt
echo redis >> required_deps.txt
echo aiohttp >> required_deps.txt
echo websockets >> required_deps.txt
echo python-dotenv >> required_deps.txt
echo tavily-python >> required_deps.txt
echo prisma >> required_deps.txt
echo upstash-redis >> required_deps.txt
echo altair >> required_deps.txt

echo.
echo ===================================================
echo Verificando dependencias necessarias:
echo ===================================================
echo [%date% %time%] Verificando dependências necessárias >> logs\check_missing_deps.log

REM Criar arquivo para dependências faltantes
echo Dependências faltantes: > missing_deps.txt

REM Verificar cada dependência
for /f %%d in (required_deps.txt) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% equ 0 (
        echo [INSTALADO] %%d
        echo [INSTALADO] %%d >> logs\check_missing_deps.log
    ) else (
        echo [FALTANDO] %%d
        echo [FALTANDO] %%d >> logs\check_missing_deps.log
        echo %%d >> missing_deps.txt
    )
)

echo.
echo ===================================================
echo Resumo da verificacao:
echo ===================================================
echo [%date% %time%] Resumo da verificação >> logs\check_missing_deps.log

REM Contar linhas no arquivo missing_deps.txt (excluindo a primeira linha)
set /a count=0
for /f "skip=1" %%a in (missing_deps.txt) do set /a count+=1

if %count% equ 0 (
    echo Todas as dependências necessárias estão instaladas!
    echo [%date% %time%] Todas as dependências necessárias estão instaladas >> logs\check_missing_deps.log
) else (
    echo Foram encontradas %count% dependências faltantes:
    echo [%date% %time%] Foram encontradas %count% dependências faltantes >> logs\check_missing_deps.log
    
    REM Mostrar dependências faltantes
    for /f "skip=1" %%a in (missing_deps.txt) do (
        echo - %%a
        echo - %%a >> logs\check_missing_deps.log
    )
    
    echo.
    echo Deseja instalar as dependências faltantes agora? (S/N)
    set /p instalar=
    if /i "%instalar%"=="S" (
        echo.
        echo Instalando dependências faltantes...
        echo [%date% %time%] Instalando dependências faltantes >> logs\check_missing_deps.log
        
        for /f "skip=1" %%a in (missing_deps.txt) do (
            echo Instalando %%a...
            echo [%date% %time%] Instalando %%a >> logs\check_missing_deps.log
            pip install %%a
            if %errorlevel% neq 0 (
                echo AVISO: Falha ao instalar %%a.
                echo [%date% %time%] AVISO: Falha ao instalar %%a >> logs\check_missing_deps.log
            ) else (
                echo %%a instalado com sucesso!
                echo [%date% %time%] %%a instalado com sucesso >> logs\check_missing_deps.log
            )
        )
        
        echo.
        echo Instalação de dependências faltantes concluída!
        echo [%date% %time%] Instalação de dependências faltantes concluída >> logs\check_missing_deps.log
    ) else (
        echo.
        echo Para instalar as dependências faltantes mais tarde, execute:
        echo pip install -r missing_deps.txt
        echo [%date% %time%] Usuário optou por não instalar dependências faltantes agora >> logs\check_missing_deps.log
    )
)

echo.
echo ===================================================
echo Verificacao de dependencias concluida!
echo ===================================================
echo [%date% %time%] Verificação de dependências concluída >> logs\check_missing_deps.log
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\check_missing_deps.log

REM Remover arquivo temporário de dependências necessárias
del required_deps.txt