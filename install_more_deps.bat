@echo off
echo ===================================================
echo Instalando Dependencias Adicionais
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo Instalando structlog...
pip install structlog

echo Instalando outras dependencias comuns...
pip install litellm sentry-sdk cryptography apscheduler croniter qstash PyPDF2 python-docx openpyxl chardet PyYAML

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend novamente...
cd backend
python api.py