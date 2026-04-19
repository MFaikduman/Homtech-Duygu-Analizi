param(
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv312\Scripts\python.exe"
$desktopRequirements = Join-Path $projectRoot "requirements-desktop.txt"
$entryPoint = Join-Path $projectRoot "src\desktop_app.py"
$iconPath = Join-Path $projectRoot "src\web_demo\app_icon.ico"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python bulunamadi: $pythonPath`nOnce .venv312 ortamini olustur."
}

if ($InstallDependencies) {
    & $pythonPath -m pip install -r $desktopRequirements
}

$pyinstallerArgs = @(
    "-m"
    "PyInstaller"
    "--noconfirm"
    "--clean"
    "--windowed"
    "--onedir"
    "--name"
    "HOMTECHMoodConsole"
    "--icon"
    $iconPath
    "--hidden-import"
    "webview.platforms.edgechromium"
    "--hidden-import"
    "webview.platforms.winforms"
    "--add-data"
    "$projectRoot\src\web_demo;src\web_demo"
    "--add-data"
    "$projectRoot\artifacts;artifacts"
    "--add-data"
    "$projectRoot\README.md;."
    $entryPoint
)

Write-Host "Masaustu uygulama paketi olusturuluyor..." -ForegroundColor Cyan
& $pythonPath $pyinstallerArgs

Write-Host ""
Write-Host "Build tamamlandi." -ForegroundColor Green
Write-Host "Cikti klasoru: dist\HOMTECHMoodConsole"
Write-Host "Calistirilabilir dosya: dist\HOMTECHMoodConsole\HOMTECHMoodConsole.exe"
