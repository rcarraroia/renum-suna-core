@echo off
echo ===================================================
echo Instalando Dependencias Finais
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo Instalando langfuse...
pip install langfuse

echo Instalando outras dependencias que podem ser necessarias...
pip install gunicorn nest-asyncio vncdotool pytesseract prometheus-client mailtrap email-validator

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend novamente...
cd backend
python api.py