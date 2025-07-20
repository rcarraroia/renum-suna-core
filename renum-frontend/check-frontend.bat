@echo off
echo ===== Verificando tipagens com TypeScript =====
call npx tsc --noEmit
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Verificação de tipagem falhou!
) else (
    echo [OK] Verificação de tipagem concluída com sucesso!
)

echo.
echo ===== Executando ESLint =====
call npx eslint . --ext .js,.jsx,.ts,.tsx
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Verificação de ESLint falhou!
) else (
    echo [OK] Verificação de ESLint concluída com sucesso!
)

echo.
echo ===== Executando build local =====
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Build falhou!
) else (
    echo [OK] Build concluído com sucesso!
)

echo.
echo ===== Verificação concluída =====