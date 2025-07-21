@echo off
echo ===================================================
echo Instalando Mais Dependencias Especificas
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo Instalando stripe...
pip install stripe==12.0.1

echo Instalando outras dependencias que podem ser necessarias...
pip install exa-py==1.9.1 e2b-code-interpreter==1.2.0 daytona-sdk==0.21.0 daytona-api-client==0.21.0 daytona-api-client-async==0.21.0 boto3==1.37.3

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend novamente...
cd backend
python api.py