@echo off
echo ===================================================
echo Verificacao de Variaveis de Ambiente
echo ===================================================
echo.

if not exist backend\.env (
    echo Arquivo .env nao encontrado. Por favor, execute setup_python_env.bat primeiro.
    exit /b 1
)

if not exist backend\.env.example (
    echo Arquivo .env.example nao encontrado. Verifique se o diretorio backend esta correto.
    exit /b 1
)

echo Comparando .env com .env.example...
echo.
echo Variaveis que podem estar faltando no seu arquivo .env:
echo.

for /f "tokens=*" %%a in ('findstr /v /c:"#" backend\.env.example') do (
    for /f "tokens=1 delims==" %%b in ("%%a") do (
        findstr /c:"%%b=" backend\.env >NUL
        if %errorlevel% neq 0 (
            echo %%a
        )
    )
)

echo.
echo Variaveis que estao no seu arquivo .env mas nao estao em .env.example:
echo.

for /f "tokens=*" %%a in ('findstr /v /c:"#" backend\.env') do (
    for /f "tokens=1 delims==" %%b in ("%%a") do (
        findstr /c:"%%b=" backend\.env.example >NUL
        if %errorlevel% neq 0 (
            echo %%a
        )
    )
)

echo.
echo ===================================================
echo Verificacao concluida!
echo ===================================================
echo.
echo Se houver variaveis faltando, adicione-as ao seu arquivo .env.
echo.
echo Pressione qualquer tecla para sair...
pause > nul