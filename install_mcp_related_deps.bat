@echo off
echo ===================================================
echo Instalando Dependencias Relacionadas ao MCP
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando instalação de dependências relacionadas ao MCP > logs\install_mcp_related.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\install_mcp_related.log
    exit /b 1
)

echo Ativando ambiente virtual Python 3.11...
echo [%date% %time%] Ativando ambiente virtual >> logs\install_mcp_related.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\install_mcp_related.log
    exit /b 1
)

echo.
echo Verificando se MCP está instalado...
echo [%date% %time%] Verificando se MCP está instalado >> logs\install_mcp_related.log
pip show mcp > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: MCP não está instalado. Instalando primeiro...
    echo [%date% %time%] MCP não está instalado, instalando... >> logs\install_mcp_related.log
    pip install mcp
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao instalar a biblioteca MCP.
        echo Verifique se o pip esta funcionando corretamente e tente novamente.
        echo [%date% %time%] ERRO: Falha ao instalar MCP >> logs\install_mcp_related.log
        exit /b 1
    )
    echo MCP instalado com sucesso!
    echo [%date% %time%] MCP instalado com sucesso >> logs\install_mcp_related.log
) else (
    echo MCP já está instalado. Continuando...
    echo [%date% %time%] MCP já está instalado >> logs\install_mcp_related.log
)

echo.
echo Instalando dependências relacionadas ao MCP...
echo [%date% %time%] Instalando dependências relacionadas ao MCP >> logs\install_mcp_related.log

REM Lista de dependências relacionadas ao MCP
echo Instalando pydantic-core...
pip install pydantic-core==2.10.1
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar pydantic-core.
    echo [%date% %time%] AVISO: Falha ao instalar pydantic-core >> logs\install_mcp_related.log
) else (
    echo pydantic-core instalado com sucesso!
    echo [%date% %time%] pydantic-core instalado com sucesso >> logs\install_mcp_related.log
)

echo Instalando typing-extensions...
pip install typing-extensions==4.7.1
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar typing-extensions.
    echo [%date% %time%] AVISO: Falha ao instalar typing-extensions >> logs\install_mcp_related.log
) else (
    echo typing-extensions instalado com sucesso!
    echo [%date% %time%] typing-extensions instalado com sucesso >> logs\install_mcp_related.log
)

echo Instalando aiohttp...
pip install aiohttp==3.8.5
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar aiohttp.
    echo [%date% %time%] AVISO: Falha ao instalar aiohttp >> logs\install_mcp_related.log
) else (
    echo aiohttp instalado com sucesso!
    echo [%date% %time%] aiohttp instalado com sucesso >> logs\install_mcp_related.log
)

echo Instalando websockets...
pip install websockets==11.0.3
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar websockets.
    echo [%date% %time%] AVISO: Falha ao instalar websockets >> logs\install_mcp_related.log
) else (
    echo websockets instalado com sucesso!
    echo [%date% %time%] websockets instalado com sucesso >> logs\install_mcp_related.log
)

echo.
echo Verificando se todas as dependências foram instaladas corretamente...
echo [%date% %time%] Verificando instalação de dependências >> logs\install_mcp_related.log

echo Verificando pydantic-core...
pip show pydantic-core > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: pydantic-core não está instalado corretamente.
    echo [%date% %time%] AVISO: pydantic-core não está instalado corretamente >> logs\install_mcp_related.log
) else (
    pip show pydantic-core | findstr "Version"
    pip show pydantic-core >> logs\install_mcp_related.log
)

echo Verificando typing-extensions...
pip show typing-extensions > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: typing-extensions não está instalado corretamente.
    echo [%date% %time%] AVISO: typing-extensions não está instalado corretamente >> logs\install_mcp_related.log
) else (
    pip show typing-extensions | findstr "Version"
    pip show typing-extensions >> logs\install_mcp_related.log
)

echo Verificando aiohttp...
pip show aiohttp > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: aiohttp não está instalado corretamente.
    echo [%date% %time%] AVISO: aiohttp não está instalado corretamente >> logs\install_mcp_related.log
) else (
    pip show aiohttp | findstr "Version"
    pip show aiohttp >> logs\install_mcp_related.log
)

echo Verificando websockets...
pip show websockets > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: websockets não está instalado corretamente.
    echo [%date% %time%] AVISO: websockets não está instalado corretamente >> logs\install_mcp_related.log
) else (
    pip show websockets | findstr "Version"
    pip show websockets >> logs\install_mcp_related.log
)

echo.
echo ===================================================
echo Instalacao de dependencias relacionadas concluida!
echo ===================================================
echo [%date% %time%] Instalação de dependências relacionadas concluída >> logs\install_mcp_related.log
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\install_mcp_related.log