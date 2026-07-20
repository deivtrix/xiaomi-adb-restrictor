@echo off
title Bloqueador de Segundo Plano - Asistente de Arranque
echo ==========================================================
echo    Optimizador ADB - Verificando Dependencias...
echo ==========================================================
echo.

:: 1. Verificar si Python está instalado en el PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    goto install_python
)

:: 2. Verificar que los módulos requeridos estén disponibles (ej. Tkinter)
python -c "import tkinter, urllib.request, concurrent.futures, json, html, re, subprocess, os, threading, time" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python y librerias de interfaz detectadas con exito.
    goto run
) else (
    echo [AVISO] Python esta instalado, pero falta soporte de interfaz grafica (Tkinter).
    echo Esto suele ocurrir si se hizo una instalacion personalizada incompleta.
    echo.
    echo Intentando reparar instalando el soporte necesario...
    winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    
    :: Volver a comprobar tras intento de reparación
    python -c "import tkinter" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Soporte reparado con exito.
        goto run
    )
    
    echo.
    echo [ERROR] No se pudo reparar automaticamente el entorno grafico.
    echo Por favor, reinstala Python desde la web oficial y asegurate de marcar
    echo la opcion "tcl/tk and IDLE" (Interfaz Grafica) en el asistente.
    echo.
    pause
    exit
)

:install_python
echo [AVISO] Python no esta instalado en esta computadora.
echo Intentando instalar Python de forma automatica y silenciosa...
echo Por favor, espera unos segundos mientras finaliza la instalacion...
echo.

winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
if %errorlevel% equ 0 (
    echo ----------------------------------------------------------
    echo [OK] Python se ha instalado correctamente en tu sistema.
    echo.
    echo IMPORTANTE: Cierra esta ventana y vuelve a hacer doble clic
    echo en INICIAR.bat para abrir el optimizador.
    echo ----------------------------------------------------------
    pause
    exit
)

echo [ERROR] No se pudo instalar Python automaticamente de forma silenciosa.
echo.
echo Por favor, sigue estos sencillos pasos para poder usar la app:
echo.
echo 1. Descarga Python desde: https://www.python.org/downloads/
echo 2. Abre el instalador descargado.
echo 3. IMPORTANTE: Marca la casilla que dice "Add python.exe to PATH" abajo.
echo 4. Haz clic en "Install Now".
echo 5. Una vez termine, vuelve a abrir INICIAR.bat.
echo.
pause
exit

:run
echo Iniciando aplicacion...
python "%~dp0recursos\src\bloquear_segundo_plano.py"
if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un problema al iniciar la aplicacion.
    pause
)
