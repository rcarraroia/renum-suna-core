@echo off
echo ===================================================
echo Gerenciamento do Backend Suna
echo ===================================================
echo.

:menu
echo Escolha uma opcao:
echo.
echo 1. Configurar ambiente Python (instalar dependencias)
echo 2. Verificar variaveis de ambiente
echo 3. Executar testes
echo 4. Iniciar backend
echo 5. Iniciar worker
echo 6. Sair
echo.
set /p opcao=Digite o numero da opcao desejada: 

if "%opcao%"=="1" (
    call setup_python_env.bat
    goto menu
)
if "%opcao%"=="2" (
    call check_env_vars.bat
    goto menu
)
if "%opcao%"=="3" (
    call run_tests.bat
    goto menu
)
if "%opcao%"=="4" (
    call start_backend.bat
    goto menu
)
if "%opcao%"=="5" (
    call start_worker.bat
    goto menu
)
if "%opcao%"=="6" (
    echo.
    echo Saindo...
    exit /b 0
)

echo.
echo Opcao invalida. Por favor, tente novamente.
echo.
goto menu