@echo off
echo ===================================================
echo Verificando Compatibilidade de Versoes
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Verificando compatibilidade de versões > logs\check_version_compatibility.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\check_version_compatibility.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\check_version_compatibility.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\check_version_compatibility.log
    exit /b 1
)

echo.
echo Criando lista de versões recomendadas...
echo [%date% %time%] Criando lista de versões recomendadas >> logs\check_version_compatibility.log

REM Lista de dependências com versões recomendadas
echo mcp=latest > recommended_versions.txt
echo fastapi=0.103.1 >> recommended_versions.txt
echo uvicorn=0.23.2 >> recommended_versions.txt
echo pydantic=1.10.8 >> recommended_versions.txt
echo dramatiq=1.14.2 >> recommended_versions.txt
echo redis=4.6.0 >> recommended_versions.txt
echo aiohttp=3.8.5 >> recommended_versions.txt
echo websockets=11.0.3 >> recommended_versions.txt
echo python-dotenv=1.0.0 >> recommended_versions.txt
echo tavily-python=0.5.4 >> recommended_versions.txt
echo prisma=0.15.0 >> recommended_versions.txt
echo upstash-redis=1.3.0 >> recommended_versions.txt
echo altair=4.2.2 >> recommended_versions.txt

echo.
echo ===================================================
echo Verificando compatibilidade de versoes:
echo ===================================================
echo [%date% %time%] Verificando compatibilidade de versões >> logs\check_version_compatibility.log

REM Criar arquivo para dependências incompatíveis
echo Dependências com versões incompatíveis: > incompatible_versions.txt

REM Verificar cada dependência
for /f "tokens=1,2 delims==" %%a in (recommended_versions.txt) do (
    echo Verificando %%a...
    pip show %%a > nul 2>&1
    if %errorlevel% equ 0 (
        REM Obter versão instalada
        for /f "tokens=2" %%v in ('pip show %%a ^| findstr "Version"') do (
            set installed_version=%%v
            
            REM Se a versão recomendada é "latest", não verificar compatibilidade
            if "%%b"=="latest" (
                echo [OK] %%a (versão !installed_version!)
                echo [OK] %%a (versão !installed_version!) >> logs\check_version_compatibility.log
            ) else (
                REM Verificar se a versão instalada é igual à recomendada
                if "!installed_version!"=="%%b" (
                    echo [OK] %%a (versão !installed_version!)
                    echo [OK] %%a (versão !installed_version!) >> logs\check_version_compatibility.log
                ) else (
                    echo [INCOMPATÍVEL] %%a (instalado: !installed_version!, recomendado: %%b)
                    echo [INCOMPATÍVEL] %%a (instalado: !installed_version!, recomendado: %%b) >> logs\check_version_compatibility.log
                    echo %%a=!installed_version!,%%b >> incompatible_versions.txt
                )
            )
        )
    ) else (
        echo [NÃO INSTALADO] %%a
        echo [NÃO INSTALADO] %%a >> logs\check_version_compatibility.log
    )
)

echo.
echo ===================================================
echo Resumo da verificacao:
echo ===================================================
echo [%date% %time%] Resumo da verificação >> logs\check_version_compatibility.log

REM Contar linhas no arquivo incompatible_versions.txt (excluindo a primeira linha)
set /a count=0
for /f "skip=1" %%a in (incompatible_versions.txt) do set /a count+=1

if %count% equ 0 (
    echo Todas as dependências instaladas têm versões compatíveis!
    echo [%date% %time%] Todas as dependências instaladas têm versões compatíveis >> logs\check_version_compatibility.log
) else (
    echo Foram encontradas %count% dependências com versões incompatíveis:
    echo [%date% %time%] Foram encontradas %count% dependências com versões incompatíveis >> logs\check_version_compatibility.log
    
    REM Mostrar dependências incompatíveis
    for /f "skip=1 tokens=1,2 delims=," %%a in (incompatible_versions.txt) do (
        echo - %%a (recomendado: %%b)
        echo - %%a (recomendado: %%b) >> logs\check_version_compatibility.log
    )
    
    echo.
    echo Deseja atualizar as dependências para as versões recomendadas? (S/N)
    set /p atualizar=
    if /i "%atualizar%"=="S" (
        echo.
        echo Atualizando dependências para versões recomendadas...
        echo [%date% %time%] Atualizando dependências para versões recomendadas >> logs\check_version_compatibility.log
        
        for /f "skip=1 tokens=1,2 delims=," %%a in (incompatible_versions.txt) do (
            for /f "tokens=1,2 delims==" %%c in ("%%a") do (
                echo Atualizando %%c para versão %%b...
                echo [%date% %time%] Atualizando %%c para versão %%b >> logs\check_version_compatibility.log
                
                REM Se a versão recomendada é "latest", instalar sem especificar versão
                if "%%b"=="latest" (
                    pip install --upgrade %%c
                ) else (
                    pip install --upgrade %%c==%%b
                )
                
                if %errorlevel% neq 0 (
                    echo AVISO: Falha ao atualizar %%c.
                    echo [%date% %time%] AVISO: Falha ao atualizar %%c >> logs\check_version_compatibility.log
                ) else (
                    echo %%c atualizado com sucesso para versão %%b!
                    echo [%date% %time%] %%c atualizado com sucesso para versão %%b >> logs\check_version_compatibility.log
                )
            )
        )
        
        echo.
        echo Atualização de dependências concluída!
        echo [%date% %time%] Atualização de dependências concluída >> logs\check_version_compatibility.log
    ) else (
        echo.
        echo Para atualizar as dependências mais tarde, você pode usar os comandos pip install.
        echo [%date% %time%] Usuário optou por não atualizar dependências agora >> logs\check_version_compatibility.log
    )
)

echo.
echo ===================================================
echo Verificacao de compatibilidade concluida!
echo ===================================================
echo [%date% %time%] Verificação de compatibilidade concluída >> logs\check_version_compatibility.log
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\check_version_compatibility.log

REM Remover arquivo temporário de versões recomendadas
del recommended_versions.txt