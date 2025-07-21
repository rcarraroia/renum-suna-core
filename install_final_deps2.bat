@echo off
echo ===================================================
echo Instalando Dependencias Finais (Parte 2)
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo Instalando tavily-python...
pip install tavily-python==0.5.4

echo Instalando outras dependencias que podem ser necessarias...
pip install prisma==0.15.0 upstash-redis==1.3.0 altair==4.2.2

echo.
echo ===================================================
echo Instalacao concluida!
echo ===================================================
echo.
echo Agora vamos tentar iniciar o backend novamente...
cd backend
python api.py