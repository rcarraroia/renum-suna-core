@echo off
echo ===================================================
echo Sincronizacao do Backend com o Repositorio Oficial Suna
echo ===================================================
echo.
echo Este script vai guiar voce pelo processo de sincronizacao
echo do diretorio backend com o repositorio oficial do Suna.
echo.
echo ATENCAO: Certifique-se de ter feito um backup do seu repositorio
echo antes de continuar.
echo.
echo Pressione CTRL+C para cancelar ou qualquer tecla para continuar...
pause > nul

echo.
echo [1/7] Verificando se o diretorio backend existe...
if not exist backend (
    echo ERRO: O diretorio backend nao foi encontrado.
    echo Certifique-se de estar executando este script na raiz do repositorio.
    exit /b 1
)
echo OK: Diretorio backend encontrado.

echo.
echo [2/7] Adicionando o repositorio oficial do Suna como remote...
git remote -v | findstr "suna-upstream" > nul
if %errorlevel% equ 0 (
    echo Remote suna-upstream ja existe. Atualizando...
    git remote set-url suna-upstream https://github.com/kortix-ai/suna.git
) else (
    git remote add suna-upstream https://github.com/kortix-ai/suna.git
)
echo OK: Remote suna-upstream configurado.

echo.
echo [3/7] Buscando as atualizacoes do repositorio oficial...
git fetch suna-upstream
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel buscar as atualizacoes do repositorio oficial.
    exit /b 1
)
echo OK: Atualizacoes buscadas com sucesso.

echo.
echo [4/7] Criando um branch temporario para a sincronizacao...
git branch | findstr "sync-backend-temp" > nul
if %errorlevel% equ 0 (
    echo Branch sync-backend-temp ja existe. Removendo...
    git checkout main
    git branch -D sync-backend-temp
)
git checkout -b sync-backend-temp
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel criar o branch temporario.
    exit /b 1
)
echo OK: Branch temporario sync-backend-temp criado.

echo.
echo [5/7] Obtendo as atualizacoes do diretorio backend...
echo ATENCAO: Este passo pode gerar conflitos que precisarao ser resolvidos manualmente.
echo.
echo Pressione qualquer tecla para continuar...
pause > nul

git checkout suna-upstream/main -- backend
if %errorlevel% neq 0 (
    echo AVISO: Podem ter ocorrido conflitos durante a obtencao das atualizacoes.
    echo Voce precisara resolver esses conflitos manualmente.
) else (
    echo OK: Atualizacoes do diretorio backend obtidas com sucesso.
)

echo.
echo [6/7] Verificando alteracoes...
git status
echo.
echo As alteracoes acima foram aplicadas ao diretorio backend.
echo Verifique se ha conflitos ou problemas que precisam ser resolvidos.
echo.
echo Pressione qualquer tecla para continuar...
pause > nul

echo.
echo [7/7] Proximos passos:
echo.
echo 1. Resolva quaisquer conflitos que possam ter surgido
echo 2. Execute os testes para verificar se tudo esta funcionando corretamente
echo 3. Se tudo estiver OK, execute os seguintes comandos:
echo    git add backend
echo    git commit -m "Sync backend with official Suna repository"
echo    git checkout main
echo    git merge sync-backend-temp
echo.
echo 4. Se houver problemas, voce pode descartar as alteracoes com:
echo    git checkout main
echo    git branch -D sync-backend-temp
echo.
echo Processo de sincronizacao concluido!
echo.
echo Pressione qualquer tecla para sair...
pause > nul