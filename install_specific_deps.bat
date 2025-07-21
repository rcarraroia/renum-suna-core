@echo off
echo ===================================================
echo Instalando Versoes Especificas de Dependencias
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo Instalando langfuse versao especifica...
pip install langfuse==2.60.5

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend novamente...
cd backend
python api.py