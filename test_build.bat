@echo off
echo Testando build do frontend...
cd renum-frontend
echo.
echo Instalando dependencias...
npm install
echo.
echo Executando build...
npm run build
echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ Build executado com sucesso!
) else (
    echo ❌ Build falhou com erro %ERRORLEVEL%
)
pause