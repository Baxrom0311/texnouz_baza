# Texnouz v2 - Windows o'rnatish skripti
# PowerShell as Administrator ishga tushiring

param(
    [string]$DbPassword = "postgres",
    [string]$RemoteDbPassword = "postgres",
    [string]$AzsName = "AZS #1",
    [int]$AzsId = 1,
    [string]$TrkPort = "COM1",
    [string]$PrinterPort = "COM2",
    [switch]$SimulateHardware = $false
)

$ErrorActionPreference = "Stop"
$InstallDir = "C:\Texnouz"
$BackendDir = "$InstallDir\backend"
$PythonExe  = "$BackendDir\venv\Scripts\python.exe"
$NssmExe    = "$InstallDir\nssm.exe"

Write-Host "=== Texnouz v2 o'rnatish ===" -ForegroundColor Cyan

# 1. Python tekshirish
Write-Host "Python tekshirilmoqda..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python topilmadi! https://python.org dan yuklab oling (3.11+)"
}
Write-Host "  OK: $($py.Source)"

# 2. PostgreSQL tekshirish
Write-Host "PostgreSQL tekshirilmoqda..."
$pg = Get-Command psql -ErrorAction SilentlyContinue
if (-not $pg) {
    Write-Warning "psql topilmadi. PostgreSQL o'rnatilganini tekshiring."
}

# 3. Fayllarni ko'chirish
Write-Host "Fayllar ko'chirilmoqda: $InstallDir"
if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
Copy-Item -Recurse -Force "$PSScriptRoot\..\.." "$BackendDir\.." -ErrorAction SilentlyContinue

# 4. .env fayl yaratish
$envContent = @"
LOCAL_DB_HOST=127.0.0.1
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=texnouz
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=$DbPassword

REMOTE_DB_HOST=3.122.18.70
REMOTE_DB_PORT=5432
REMOTE_DB_NAME=mms_localhost
REMOTE_DB_USER=postgres
REMOTE_DB_PASSWORD=$RemoteDbPassword

AZS_ID=$AzsId
AZS_NAME=$AzsName

TRK_PORT=$TrkPort
TRK_BAUD=9600
PRINTER_PORT=$PrinterPort
PRINTER_BAUD=9600

SIMULATE_HARDWARE=$($SimulateHardware.ToString().ToLower())

API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$(New-Guid)

RECEIPT_HEADER=Товарный чек
"@
$envContent | Out-File "$BackendDir\.env" -Encoding UTF8
Write-Host "  .env fayl yaratildi"

# 5. Virtual environment
Write-Host "Python venv yaratilmoqda..."
Set-Location $BackendDir
python -m venv venv
& "$BackendDir\venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "  Dependencies o'rnatildi"

# 6. PostgreSQL bazasini yaratish
Write-Host "PostgreSQL bazasi yaratilmoqda..."
$env:PGPASSWORD = $DbPassword
psql -U postgres -c "CREATE DATABASE texnouz;" 2>$null
Write-Host "  texnouz DB tayyor"

# 7. NSSM yuklab olish (agar yo'q bo'lsa)
if (-not (Test-Path $NssmExe)) {
    Write-Host "NSSM yuklanmoqda..."
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $zipPath = "$env:TEMP\nssm.zip"
    Invoke-WebRequest $nssmUrl -OutFile $zipPath
    Expand-Archive $zipPath "$env:TEMP\nssm" -Force
    Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" $NssmExe
    Write-Host "  NSSM tayyor"
}

# 8. TexnouzBackend servisi
Write-Host "TexnouzBackend servisi o'rnatilmoqda..."
& $NssmExe stop TexnouzBackend 2>$null
& $NssmExe remove TexnouzBackend confirm 2>$null
& $NssmExe install TexnouzBackend $PythonExe
& $NssmExe set TexnouzBackend AppParameters "run.py"
& $NssmExe set TexnouzBackend AppDirectory $BackendDir
& $NssmExe set TexnouzBackend AppEnvironmentExtra "PYTHONPATH=$BackendDir"
& $NssmExe set TexnouzBackend DisplayName "Texnouz v2 Backend"
& $NssmExe set TexnouzBackend Start SERVICE_AUTO_START
& $NssmExe set TexnouzBackend AppStdout "$InstallDir\logs\backend.log"
& $NssmExe set TexnouzBackend AppStderr "$InstallDir\logs\backend_err.log"

# 9. TexnouzSync servisi (mavjud sync bridge)
Write-Host "TexnouzSync servisi o'rnatilmoqda..."
& $NssmExe stop TexnouzSync 2>$null
& $NssmExe remove TexnouzSync confirm 2>$null
& $NssmExe install TexnouzSync $PythonExe
& $NssmExe set TexnouzSync AppParameters "main.py"
& $NssmExe set TexnouzSync AppDirectory "$InstallDir\sync"
& $NssmExe set TexnouzSync DisplayName "Texnouz v2 Sync"
& $NssmExe set TexnouzSync Start SERVICE_AUTO_START
& $NssmExe set TexnouzSync AppStdout "$InstallDir\logs\sync.log"

# 10. Loglar papkasi
New-Item -ItemType Directory -Force -Path "$InstallDir\logs" | Out-Null

# 11. Servislarni ishga tushirish
Write-Host "Servislar ishga tushirilmoqda..."
Start-Sleep 2
& $NssmExe start TexnouzBackend
Start-Sleep 3
& $NssmExe start TexnouzSync

# 12. Desktop shortcut
Write-Host "Desktop shortcut yaratilmoqda..."
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Texnouz v2.lnk")
$Shortcut.TargetPath = "chrome"
$Shortcut.Arguments = "--app=http://localhost:8000 --start-maximized"
$Shortcut.Description = "Texnouz v2 AZS Tizimi"
$Shortcut.Save()

Write-Host ""
Write-Host "=== O'RNATISH TUGADI ===" -ForegroundColor Green
Write-Host "  Brauzer: http://localhost:8000"
Write-Host "  Parol:   1111 (admin)"
Write-Host "  Loglar:  $InstallDir\logs\"
Write-Host ""
Write-Host "Servislarni tekshirish:" -ForegroundColor Yellow
Write-Host "  Get-Service TexnouzBackend"
Write-Host "  Get-Service TexnouzSync"
