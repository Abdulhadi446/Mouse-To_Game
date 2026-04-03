$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

py -3 -m pip install -r requirements.txt -r requirements-build.txt

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name mouse-to-game.exe mouse_to_wasd.py
py -3 -m PyInstaller --noconfirm --clean --onefile --name input-remapper-runner.exe input_remapper_runner.py

Write-Host "Build complete. Executables are in dist/"
Get-ChildItem dist | Format-Table Name, Length
