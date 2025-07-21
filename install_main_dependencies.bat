@echo off
echo ===================================================
echo Instalando Dependencias Principais
echo ===================================================
echo.

REM Verificar se o log existe e criar diretório se necessário
if not exist logs\ (
    mkdir logs
)

REM Iniciar log
echo [%date% %time%] Iniciando instalação de dependências principais > logs\install_main_deps.log

if not exist backend\venv311 (
    echo ERRO: Ambiente virtual Python 3.11 nao encontrado em backend\venv311
    echo Por favor, execute setup_complete_noninteractive.bat primeiro para criar o ambiente virtual.
    echo [%date% %time%] ERRO: Ambiente virtual não encontrado >> logs\install_main_deps.log
    exit /b 1
)

echo Verificando versao do Python...
echo [%date% %time%] Verificando versão do Python >> logs\install_main_deps.log
call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    echo [%date% %time%] ERRO: Falha ao ativar o ambiente virtual >> logs\install_main_deps.log
    exit /b 1
)

python --version | findstr "3.11" > nul
if %errorlevel% neq 0 (
    echo AVISO: A versao do Python pode nao ser 3.11. Isso pode causar problemas.
    echo Versao atual:
    python --version
    python --version >> logs\install_main_deps.log
    echo.
    echo Deseja continuar mesmo assim? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo Instalacao cancelada pelo usuario.
        echo [%date% %time%] Instalação cancelada pelo usuário >> logs\install_main_deps.log
        exit /b 1
    )
)

echo.
echo Instalando dependencias principais do FastAPI...
echo [%date% %time%] Instalando dependências principais do FastAPI >> logs\install_main_deps.log

echo Instalando fastapi...
pip install fastapi==0.115.12
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar fastapi.
    echo [%date% %time%] ERRO: Falha ao instalar fastapi >> logs\install_main_deps.log
    goto error
) else (
    echo fastapi instalado com sucesso!
    echo [%date% %time%] fastapi instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando uvicorn...
pip install uvicorn[standard]==0.27.1
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar uvicorn.
    echo [%date% %time%] ERRO: Falha ao instalar uvicorn >> logs\install_main_deps.log
    goto error
) else (
    echo uvicorn instalado com sucesso!
    echo [%date% %time%] uvicorn instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando pydantic...
pip install pydantic==1.10.8
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar pydantic.
    echo [%date% %time%] ERRO: Falha ao instalar pydantic >> logs\install_main_deps.log
    goto error
) else (
    echo pydantic instalado com sucesso!
    echo [%date% %time%] pydantic instalado com sucesso >> logs\install_main_deps.log
)

echo.
echo Instalando dependencias de ambiente...
echo [%date% %time%] Instalando dependências de ambiente >> logs\install_main_deps.log

echo Instalando python-dotenv...
pip install python-dotenv==1.0.1
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar python-dotenv.
    echo [%date% %time%] AVISO: Falha ao instalar python-dotenv >> logs\install_main_deps.log
) else (
    echo python-dotenv instalado com sucesso!
    echo [%date% %time%] python-dotenv instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando httpx...
pip install httpx==0.28.0
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar httpx.
    echo [%date% %time%] AVISO: Falha ao instalar httpx >> logs\install_main_deps.log
) else (
    echo httpx instalado com sucesso!
    echo [%date% %time%] httpx instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando python-multipart...
pip install python-multipart==0.0.20
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar python-multipart.
    echo [%date% %time%] AVISO: Falha ao instalar python-multipart >> logs\install_main_deps.log
) else (
    echo python-multipart instalado com sucesso!
    echo [%date% %time%] python-multipart instalado com sucesso >> logs\install_main_deps.log
)

echo.
echo Instalando dependencias de banco de dados...
echo [%date% %time%] Instalando dependências de banco de dados >> logs\install_main_deps.log

echo Instalando supabase...
pip install supabase==2.17.0
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar supabase.
    echo [%date% %time%] AVISO: Falha ao instalar supabase >> logs\install_main_deps.log
) else (
    echo supabase instalado com sucesso!
    echo [%date% %time%] supabase instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando redis...
pip install redis==5.2.1
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar redis.
    echo [%date% %time%] AVISO: Falha ao instalar redis >> logs\install_main_deps.log
) else (
    echo redis instalado com sucesso!
    echo [%date% %time%] redis instalado com sucesso >> logs\install_main_deps.log
)

echo.
echo Instalando dependencias de processamento em background...
echo [%date% %time%] Instalando dependências de processamento em background >> logs\install_main_deps.log

echo Instalando dramatiq...
pip install dramatiq==1.18.0
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar dramatiq.
    echo [%date% %time%] AVISO: Falha ao instalar dramatiq >> logs\install_main_deps.log
) else (
    echo dramatiq instalado com sucesso!
    echo [%date% %time%] dramatiq instalado com sucesso >> logs\install_main_deps.log
)

echo Instalando pika...
pip install pika==1.3.2
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar pika.
    echo [%date% %time%] AVISO: Falha ao instalar pika >> logs\install_main_deps.log
) else (
    echo pika instalado com sucesso!
    echo [%date% %time%] pika instalado com sucesso >> logs\install_main_deps.log
)

echo.
echo Verificando se todas as dependencias principais foram instaladas...
echo [%date% %time%] Verificando instalação de dependências principais >> logs\install_main_deps.log

set deps_ok=1
for %%d in (fastapi uvicorn pydantic python-dotenv httpx supabase redis dramatiq) do (
    echo Verificando %%d...
    pip show %%d > nul 2>&1
    if %errorlevel% neq 0 (
        echo AVISO: %%d nao esta instalado corretamente.
        echo [%date% %time%] AVISO: %%d não está instalado corretamente >> logs\install_main_deps.log
        set deps_ok=0
    ) else (
        pip show %%d | findstr "Version"
        pip show %%d >> logs\install_main_deps.log
    )
)

echo.
echo Instalando dependencias do projeto...
echo [%date% %time%] Instalando dependências do projeto >> logs\install_main_deps.log
cd backend
pip install -e .
if %errorlevel% neq 0 (
    echo AVISO: Falha ao instalar as dependencias do projeto.
    echo Verifique as mensagens de erro acima e tente instalar manualmente se necessario.
    echo [%date% %time%] AVISO: Falha ao instalar dependências do projeto >> logs\install_main_deps.log
) else (
    echo Dependências do projeto instaladas com sucesso!
    echo [%date% %time%] Dependências do projeto instaladas com sucesso >> logs\install_main_deps.log
)
cd ..

echo.
echo ===================================================
echo Instalacao de dependencias principais concluida!
echo ===================================================
echo [%date% %time%] Instalação de dependências principais concluída >> logs\install_main_deps.log

if %deps_ok% equ 0 (
    echo.
    echo AVISO: Algumas dependencias podem nao ter sido instaladas corretamente.
    echo Verifique os logs em logs\install_main_deps.log para mais detalhes.
    echo [%date% %time%] AVISO: Algumas dependências podem não ter sido instaladas corretamente >> logs\install_main_deps.log
)

echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\install_main_deps.log
goto end

:error
echo.
echo ===================================================
echo Falha na instalacao de dependencias principais!
echo ===================================================
echo [%date% %time%] Falha na instalação de dependências principais >> logs\install_main_deps.log
echo.
echo Desativando ambiente virtual...
deactivate
echo [%date% %time%] Ambiente virtual desativado >> logs\install_main_deps.log

:end