@echo off
echo ===================================================
echo Iniciando o Backend Suna (Configuracao Final)
echo ===================================================
echo.

call backend\venv311\Scripts\activate.bat

echo.
echo Iniciando o backend...
cd backend
python api.py