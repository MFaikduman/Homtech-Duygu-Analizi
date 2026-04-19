param()

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv312\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python bulunamadi: $pythonPath`nOnce .venv312 ortamini olustur."
}

Write-Host "HOMTECH masaustu uygulamasi baslatiliyor..." -ForegroundColor Cyan
Start-Process `
    -FilePath $pythonPath `
    -ArgumentList "-m", "src.desktop_app" `
    -WorkingDirectory $projectRoot
