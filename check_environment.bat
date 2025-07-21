@echo off
echo ===================================================
echo Verificando Ambiente Existente
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Verificando ambiente existente > logs\check_environment.log

echo Verificando componentes do ambiente...
echo [%date% %time%] Verificando componentes do ambiente >> logs\check_environment.log

REM Verificar Python
echo Verificando Python...
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [FALTANDO] Python nao encontrado no PATH
    echo [%date% %time%] ERRO: Python não encontrado no PATH >> logs\check_environment.log
) else (
    python --version > temp_version.txt 2>&1
    set /p python_version=<temp_version.txt
    echo [INSTALADO] %python_version%
    echo [%date% %time%] INFO: %python_version% >> logs\check_environment.log
    del temp_version.txt
)

REM Verificar ambiente virtual
echo Verificando ambiente virtual...
if exist backend\venv311 (
    echo [INSTALADO] Ambiente virtual Python 3.11 (backend\venv311)
    echo [%date% %time%] INFO: Ambiente virtual Python 3.11 encontrado >> logs\check_environment.log
) else (
    echo [FALTANDO] Ambiente virtual Python 3.11 (backend\venv311)
    echo [%date% %time%] AVISO: Ambiente virtual Python 3.11 não encontrado >> logs\check_environment.log
)

REM Verificar arquivo .env
echo Verificando arquivo .env...
if exist backend\.env (
    echo [INSTALADO] Arquivo .env
    echo [%date% %time%] INFO: Arquivo .env encontrado >> logs\check_environment.log
) else (
    echo [FALTANDO] Arquivo .env
    echo [%date% %time%] AVISO: Arquivo .env não encontrado >> logs\check_environment.log
)

REM Verificar diretório backend
echo Verificando diretorio backend...
if exist backend (
    echo [INSTALADO] Diretorio backend
    echo [%date% %time%] INFO: Diretório backend encontrado >> logs\check_environment.log
) else (
    echo [FALTANDO] Diretorio backend
    echo [%date% %time%] ERRO: Diretório backend não encontrado >> logs\check_environment.log
)

echo.
echo ===================================================
echo Verificando dependencias principais...
echo ===================================================
echo [%date% %time%] Verificando dependências principais >> logs\check_environment.log

REM Verificar se o ambiente virtual existe antes de verificar dependências
if exist backend\venv311 (
    echo Ativando ambiente virtual...
    call backend\venv311\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao ativar o ambiente virtual
        echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\check_environment.log
    ) else (
        REM Lista de dependências principais para verificar
        set deps=mcp fastapi uvicorn pydantic dramatiq redis

        for %%d in (%deps%) do (
            echo Verificando %%d...
            pip show %%d > nul 2>&1
            if %errorlevel% equ 0 (
                for /f "tokens=2" %%v in ('pip show %%d ^| findstr "Version"') do (
                    echo [INSTALADO] %%d (versao %%v)
                    echo [%date% %time%] INFO: %%d (versão %%v) instalado >> logs\check_environment.log
                )
            ) else (
                echo [FALTANDO] %%d
                echo [%date% %time%] AVISO: %%d não instalado >> logs\check_environment.log
            )
        )

        echo.
        echo Desativando ambiente virtual...
        deactivate
    )
) else (
    echo Ambiente virtual nao encontrado, pulando verificacao de dependencias.
    echo [%date% %time%] AVISO: Ambiente virtual não encontrado, pulando verificação de dependências >> logs\check_environment.log
)

echo.
echo ===================================================
echo Resumo da verificacao:
echo ===================================================
echo [%date% %time%] Resumo da verificação >> logs\check_environment.log

REM Verificar se há problemas críticos
set critical_issues=0

REM Verificar Python
where python > nul 2>&1
if %errorlevel% neq 0 set /a critical_issues+=1

REM Verificar diretório backend
if not exist backend set /a critical_issues+=1

if %critical_issues% gtr 0 (
    echo [AVISO] Foram encontrados %critical_issues% problemas criticos que precisam ser resolvidos.
    echo [%date% %time%] AVISO: Foram encontrados %critical_issues% problemas críticos >> logs\check_environment.log
    
    echo.
    echo Recomendacoes:
    echo [%date% %time%] Recomendações: >> logs\check_environment.log
    
    where python > nul 2>&1
    if %errorlevel% neq 0 (
        echo - Instale Python 3.11+ e adicione-o ao PATH
        echo [%date% %time%] - Instale Python 3.11+ e adicione-o ao PATH >> logs\check_environment.log
    )
    
    if not exist backend (
        echo - Verifique se o diretorio backend existe
        echo [%date% %time%] - Verifique se o diretório backend existe >> logs\check_environment.log
    )
) else (
    echo [OK] Nenhum problema critico encontrado.
    echo [%date% %time%] INFO: Nenhum problema crítico encontrado >> logs\check_environment.log
    
    REM Verificar problemas não críticos
    set non_critical_issues=0
    
    if not exist backend\venv311 set /a non_critical_issues+=1
    if not exist backend\.env set /a non_critical_issues+=1
    
    if %non_critical_issues% gtr 0 (
        echo [AVISO] Foram encontrados %non_critical_issues% problemas nao criticos.
        echo [%date% %time%] AVISO: Foram encontrados %non_critical_issues% problemas não críticos >> logs\check_environment.log
        
        echo.
        echo Recomendacoes:
        echo [%date% %time%] Recomendações: >> logs\check_environment.log
        
        if not exist backend\venv311 (
            echo - Execute setup_complete_noninteractive.bat para criar o ambiente virtual
            echo [%date% %time%] - Execute setup_complete_noninteractive.bat para criar o ambiente virtual >> logs\check_environment.log
        )
        
        if not exist backend\.env (
            echo - Crie o arquivo backend\.env com as variaveis de ambiente necessarias
            echo [%date% %time%] - Crie o arquivo backend\.env com as variáveis de ambiente necessárias >> logs\check_environment.log
        )
    ) else (
        echo [OK] Nenhum problema nao critico encontrado.
        echo [%date% %time%] INFO: Nenhum problema não crítico encontrado >> logs\check_environment.log
    )
)

echo.
echo ===================================================
echo Verificacao de ambiente concluida!
echo ===================================================
echo [%date% %time%] Verificação de ambiente concluída >> logs\check_environment.log