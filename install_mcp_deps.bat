@echo off
echo ===================================================
echo Instalando Biblioteca MCP e Dependencias Faltantes
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando instalação da biblioteca MCP > logs\install_mcp.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\install_mcp.log
    exit /b 1
)

echo Verificando versao do Python...
echo [%date% %time%] Verificando versão do Python >> logs\install_mcp.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\install_mcp.log
    exit /b 1
)

python --version | findstr "3.11" > nul
if %errorlevel% neq 0 (
    echo AVISO: A versao do Python pode nao ser 3.11. Isso pode causar problemas.
    echo Versao atual:
    python --version
    python --version >> logs\install_mcp.log
    echo.
    echo Deseja continuar mesmo assim? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo Instalacao cancelada pelo usuario.
        echo [%date% %time%] Instalação cancelada pelo usuário >> logs\install_mcp.log
        exit /b 1
    )
)

echo.
echo Verificando se MCP já está instalado...
echo [%date% %time%] Verificando se MCP já está instalado >> logs\install_mcp.log
pip show mcp > nul 2>&1
if %errorlevel% equ 0 (
    echo MCP já está instalado. Verificando versão...
    pip show mcp | findstr "Version"
    pip show mcp >> logs\install_mcp.log
    
    echo Deseja reinstalar o MCP? (S/N)
    set /p reinstalar=
    if /i not "%reinstalar%"=="S" (
        echo Pulando instalação do MCP.
        echo [%date% %time%] Instalação do MCP pulada (já instalado) >> logs\install_mcp.log
        goto skip_mcp
    )
)

echo Instalando mcp...
echo [%date% %time%] Instalando MCP >> logs\install_mcp.log
pip install mcp
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar a biblioteca MCP.
    echo Verifique se o pip esta funcionando corretamente e tente novamente.
    echo [%date% %time%] ERRO: Falha ao instalar MCP >> logs\install_mcp.log
    exit /b 1
)

echo MCP instalado com sucesso!
echo [%date% %time%] MCP instalado com sucesso >> logs\install_mcp.log

:skip_mcp

echo.
echo Instalando outras dependencias que podem estar faltando...
echo [%date% %time%] Instalando outras dependências >> logs\install_mcp.log
pip install fastapi-cli uvicorn[standard] python-dotenv pydantic==1.10.8
if %errorlevel% neq 0 (
    echo AVISO: Algumas dependencias podem nao ter sido instaladas corretamente.
    echo Verifique as mensagens de erro acima e tente instalar manualmente se necessario.
    echo [%date% %time%] AVISO: Problemas na instalação de dependências adicionais >> logs\install_mcp.log
) else (
    echo Dependências adicionais instaladas com sucesso!
    echo [%date% %time%] Dependências adicionais instaladas com sucesso >> logs\install_mcp.log
)

echo.
echo Verificando dependencias do projeto...
echo [%date% %time%] Verificando dependências do projeto >> logs\install_mcp.log
cd backend
pip install -e .
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar as dependencias do projeto.
    echo Verifique as mensagens de erro acima e tente instalar manualmente se necessario.
    echo [%date% %time%] AVISO: Falha ao instalar dependências do projeto >> logs\install_mcp.log
) else (
    echo Dependências do projeto instaladas com sucesso!
    echo [%date% %time%] Dependências do projeto instaladas com sucesso >> logs\install_mcp.log
)
cd ..

echo.
echo Verificando se MCP está funcionando corretamente...
echo [%date% %time%] Verificando funcionamento do MCP >> logs\install_mcp.log
python -c "import mcp; print('MCP importado com sucesso: versão', mcp.__version__)" > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: MCP instalado, mas pode haver problemas ao importá-lo.
    echo Tente executar o backend para verificar se tudo está funcionando corretamente.
    echo [%date% %time%] AVISO: Possíveis problemas ao importar MCP >> logs\install_mcp.log
) else (
    python -c "import mcp; print('MCP importado com sucesso: versão', mcp.__version__)"
    python -c "import mcp; print('MCP importado com sucesso: versão', mcp.__version__)" >> logs\install_mcp.log
)

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo [%date% %time%] Instalação concluída com sucesso >> logs\install_mcp.log
echo.
echo Deseja iniciar o backend agora? (S/N)
set /p iniciar=
if /i "%iniciar%"=="S" (
    echo Iniciando o backend...
    echo [%date% %time%] Iniciando o backend >> logs\install_mcp.log
    cd backend
    python api.py
    cd ..
) else (
    echo Para iniciar o backend mais tarde, execute start_backend_final.bat
    echo [%date% %time%] Usuário optou por não iniciar o backend agora >> logs\install_mcp.log
)

echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\install_mcp.log