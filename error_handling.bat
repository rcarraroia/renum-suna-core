@echo off
REM Este script contém funções para tratamento de erros

:log_error
REM Parâmetros: %1 - Mensagem de erro, %2 - Arquivo de log
echo [%date% %time%] ERRO: %~1 >> %~2
echo ERRO: %~1
exit /b 1

:log_warning
REM Parâmetros: %1 - Mensagem de aviso, %2 - Arquivo de log
echo [%date% %time%] AVISO: %~1 >> %~2
echo AVISO: %~1
exit /b 0

:log_info
REM Parâmetros: %1 - Mensagem informativa, %2 - Arquivo de log
echo [%date% %time%] INFO: %~1 >> %~2
echo INFO: %~1
exit /b 0

:check_environment
REM Verifica se o ambiente está configurado corretamente
REM Parâmetros: %1 - Arquivo de log
if not exist backend\venv311 (
    call :log_error "Ambiente virtual Python 3.11 nao encontrado em backend\venv311. Execute setup_complete_noninteractive.bat primeiro." %~1
    exit /b 1
)

call backend\venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    call :log_error "Falha ao ativar o ambiente virtual." %~1
    exit /b 1
)

python --version | findstr "3.11" > nul
if %errorlevel% neq 0 (
    call :log_warning "A versao do Python pode nao ser 3.11. Isso pode causar problemas." %~1
    echo Versao atual:
    python --version
    exit /b 1
)

exit /b 0

:check_file_exists
REM Verifica se um arquivo existe
REM Parâmetros: %1 - Caminho do arquivo, %2 - Mensagem de erro, %3 - Arquivo de log
if not exist %~1 (
    call :log_error "%~2" %~3
    exit /b 1
)
exit /b 0