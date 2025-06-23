@echo off
echo ========================================
echo  SYSCOM SHOPIFY IMPORTER - CONSTRUCTOR
echo ========================================
echo.

echo Instalando dependencias necesarias...
pip install pyinstaller
pip install -r requirements.txt

echo.
echo Construyendo ejecutable...
python build_executable.py

echo.
echo Presione cualquier tecla para continuar...
pause
