@echo off
echo ===================================
echo     CONSTRUINDO EXECUTAVEL PDV3
echo ===================================

REM Limpar builds anteriores
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "PDV.spec" del "PDV.spec"

echo.
echo Instalando dependencias do PyInstaller...
pip install pyinstaller

echo.
echo Construindo executavel...
pyinstaller --noconsole ^
  --name "PDV" ^
  --icon=assets/icon.ico ^
  --add-data "assets/icon.ico;assets" ^
  --add-data "database;database" ^
  --add-data "views;views" ^
  --add-data "utils;utils" ^
  --add-data "repositories;repositories" ^
  --hidden-import=flet ^
  --hidden-import=sqlite3 ^
  --hidden-import=httpx ^
  --hidden-import=asyncio ^
  --hidden-import=json ^
  --hidden-import=uuid ^
  --hidden-import=datetime ^
  --hidden-import=os ^
  --hidden-import=platform ^
  --hidden-import=traceback ^
  --hidden-import=sys ^
  main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo   EXECUTAVEL CRIADO COM SUCESSO!
    echo ===================================
    echo.
    echo Executavel disponivel em: dist\PDV\PDV.exe
    echo.
    pause
) else (
    echo.
    echo ===================================
    echo      ERRO AO CRIAR EXECUTAVEL
    echo ===================================
    echo.
    pause
)
