param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoBrowser,
    [switch]$WaitForReady
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv312\Scripts\python.exe"
$modelPath = Join-Path $projectRoot "artifacts\emotion_cnn.keras"
$reportsDir = Join-Path $projectRoot "reports"
$healthUrl = "http://{0}:{1}/api/health" -f $HostAddress, $Port
$appUrl = "http://{0}:{1}/" -f $HostAddress, $Port

New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python bulunamadi: $pythonPath`nOnce .venv312 ortamini olustur."
}

if (-not (Test-Path -LiteralPath $modelPath)) {
    Write-Warning "Model dosyasi bulunamadi: $modelPath"
    Write-Warning "Arayuz acilsa bile analiz modu yerine yalnizca senaryo modu calisabilir."
}

$serverArgs = @(
    "-m"
    "src.demo_web"
    "--host"
    $HostAddress
    "--port"
    $Port
)

$stdoutPath = Join-Path $reportsDir "demo_web.out.log"
$stderrPath = Join-Path $reportsDir "demo_web.err.log"

Write-Host "HOMTECH demo baslatiliyor..." -ForegroundColor Cyan
Write-Host "Adres: $appUrl"

$serverProcess = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList $serverArgs `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

if ($WaitForReady) {
    $health = $null
    for ($attempt = 0; $attempt -lt 45 -and -not $health; $attempt++) {
        Start-Sleep -Seconds 1
        try {
            $health = Invoke-RestMethod -Uri $healthUrl
        } catch {
        }
    }

    if (-not $health) {
        if ($serverProcess -and -not $serverProcess.HasExited) {
            Stop-Process -Id $serverProcess.Id -Force
        }

        throw "Demo baslatildi ama saglik kontrolu donmedi. Loglari kontrol et: reports\demo_web.out.log ve reports\demo_web.err.log"
    }

    Write-Host "Sunucu hazir." -ForegroundColor Green
    Write-Host ("Model hazir: {0}" -f $health.model_ready)
    Write-Host ("Model yukleniyor: {0}" -f $health.model_loading)
    Write-Host ("Senaryo hazir: {0}" -f $health.scenario_ready)
} else {
    Write-Host "Sunucu arka planda baslatildi." -ForegroundColor Green
    Write-Host "Web arayuzu hemen acilir; model arka planda yuklenir."
}

if (-not $NoBrowser) {
    Start-Process $appUrl | Out-Null
}

Write-Host ""
Write-Host "Tarayicida ac: $appUrl"
Write-Host "Sunucuyu durdurmak icin: Stop-Process -Id $($serverProcess.Id)"
Write-Host ("Arka plan process id: {0}" -f $serverProcess.Id)
