@echo off
echo ===== Preparando Backend Renum para Deploy =====

echo.
echo === Limpando arquivos desnecessários ===
echo Removendo __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Removendo .pytest_cache...
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"

echo Removendo arquivos .pyc...
del /s /q *.pyc

echo.
echo === Verificando requirements.txt ===
echo Certifique-se de que o arquivo requirements.txt está atualizado!

echo.
echo === Verificando .env.example ===
echo Certifique-se de que o arquivo .env.example contém todas as variáveis necessárias!

echo.
echo === Criando pacote para deploy ===
echo Criando diretório temporário...
if not exist "deploy" mkdir deploy

echo Copiando arquivos para diretório de deploy...
xcopy /E /I /Y app deploy\app
copy requirements.txt deploy\
copy .env.example deploy\
copy start.sh deploy\

echo Criando arquivo README para deploy...
echo # Renum Backend > deploy\README.md
echo. >> deploy\README.md
echo ## Instalação >> deploy\README.md
echo. >> deploy\README.md
echo 1. Copie o arquivo .env.example para .env e configure as variáveis de ambiente >> deploy\README.md
echo 2. Instale as dependências: `pip install -r requirements.txt` >> deploy\README.md
echo 3. Execute o servidor: `bash start.sh` >> deploy\README.md
echo. >> deploy\README.md
echo ## Portas >> deploy\README.md
echo. >> deploy\README.md
echo O servidor será executado na porta 9000 por padrão. >> deploy\README.md
echo Você pode alterar a porta no arquivo start.sh. >> deploy\README.md

echo.
echo === Compactando arquivos para deploy ===
echo Criando arquivo ZIP...
powershell Compress-Archive -Path deploy\* -DestinationPath renum-backend-deploy.zip -Force

echo Removendo diretório temporário...
rd /s /q deploy

echo.
echo === Deploy preparado com sucesso! ===
echo O arquivo renum-backend-deploy.zip está pronto para ser enviado para a VPS.
echo.