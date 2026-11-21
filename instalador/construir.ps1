# Genera el ejecutable (PyInstaller) y el instalador (Inno Setup 6).
# Uso, desde la carpeta "Aplicativo Sobretiempos":  powershell -File instalador\construir.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# 1. Ejecutable en carpeta (dist\RegistroSobretiempos\RegistroSobretiempos.exe)
python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name RegistroSobretiempos `
    --icon app\recursos\icono.ico `
    --paths app `
    --add-data "app\recursos;recursos" `
    --exclude-module lxml --exclude-module PIL --exclude-module numpy --exclude-module pandas `
    --exclude-module matplotlib --exclude-module cryptography `
    --distpath dist --workpath build `
    app\main.py

# 2. Instalador (instalador\salida\Instalador_RegistroSobretiempos_1.0.0.exe)
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
          "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
          "C:\Program Files\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "No se encontró Inno Setup 6 (ISCC.exe)." }
& $iscc instalador\instalador.iss
