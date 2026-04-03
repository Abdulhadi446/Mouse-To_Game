@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [1/3] Installing build dependencies...
py -3 -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :error

echo [2/3] Building mouse-to-game.exe...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all pynput --name mouse-to-game.exe mouse_to_wasd.py
if errorlevel 1 goto :error

echo [3/3] Building input-remapper-runner.exe...
py -3 -m PyInstaller --noconfirm --clean --onefile --collect-all pynput --name input-remapper-runner.exe input_remapper_runner.py
if errorlevel 1 goto :error

echo.
echo Build complete. Executables are in dist\
dir /b dist
goto :eof

:error
echo.
echo Build failed with exit code %errorlevel%.
exit /b %errorlevel%
