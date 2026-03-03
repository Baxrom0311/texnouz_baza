[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$NssmExe,

    [string]$ServiceName = "MMSBridge",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$AppPath = "",
    [string]$LogsDir = "",

    [string]$LocalDbName = "texnouz_copy",
    [string]$LocalDbUser = "baxrom",
    [string]$LocalDbPassword = "",
    [string]$LocalDbHost = "127.0.0.1",
    [int]$LocalDbPort = 5432,

    [string]$RemoteDbName = "mms_localhost",
    [string]$RemoteDbUser = "sync_user1",
    [string]$RemoteDbPassword = "",
    [string]$RemoteDbHost = "3.122.18.70",
    [int]$RemoteDbPort = 5432,

    [string]$SyncFromDateTime = "2026-03-01 00:00:00",
    [int]$BatchSize = 1000,
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $NssmExe)) {
    throw "NSSM topilmadi: $NssmExe"
}

if ([string]::IsNullOrWhiteSpace($AppPath)) {
    $AppPath = Join-Path $ProjectRoot "dist\mms_bridge.exe"
}
if (-not (Test-Path $AppPath)) {
    throw "Exe topilmadi: $AppPath"
}

if ([string]::IsNullOrWhiteSpace($LogsDir)) {
    $LogsDir = Join-Path $ProjectRoot "logs"
}
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$stdoutPath = Join-Path $LogsDir "mms_bridge.out.log"
$stderrPath = Join-Path $LogsDir "mms_bridge.err.log"

function Invoke-Nssm {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]]$Args)
    & $NssmExe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "NSSM xatosi: $($Args -join ' ')"
    }
}

$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -eq $existingService) {
    Invoke-Nssm install $ServiceName $AppPath
}

Invoke-Nssm set $ServiceName Application $AppPath
Invoke-Nssm set $ServiceName AppDirectory $ProjectRoot
Invoke-Nssm set $ServiceName AppParameters ""
Invoke-Nssm set $ServiceName Start SERVICE_AUTO_START
Invoke-Nssm set $ServiceName DependOnService Tcpip
Invoke-Nssm set $ServiceName ObjectName LocalSystem

Invoke-Nssm set $ServiceName AppStdout $stdoutPath
Invoke-Nssm set $ServiceName AppStderr $stderrPath
Invoke-Nssm set $ServiceName AppRotateFiles 1
Invoke-Nssm set $ServiceName AppRotateOnline 1
Invoke-Nssm set $ServiceName AppRotateBytes 10485760

Invoke-Nssm set $ServiceName AppExit Default Restart
Invoke-Nssm set $ServiceName AppThrottle 15000
Invoke-Nssm set $ServiceName AppRestartDelay 5000
Invoke-Nssm set $ServiceName AppStopMethodConsole 15000
Invoke-Nssm set $ServiceName AppStopMethodWindow 15000
Invoke-Nssm set $ServiceName AppStopMethodThreads 15000
Invoke-Nssm set $ServiceName AppStopMethodSkip 0

$envPairs = @(
    "LOCAL_DB_NAME=$LocalDbName"
    "LOCAL_DB_USER=$LocalDbUser"
    "LOCAL_DB_PASSWORD=$LocalDbPassword"
    "LOCAL_DB_HOST=$LocalDbHost"
    "LOCAL_DB_PORT=$LocalDbPort"
    "REMOTE_DB_NAME=$RemoteDbName"
    "REMOTE_DB_USER=$RemoteDbUser"
    "REMOTE_DB_PASSWORD=$RemoteDbPassword"
    "REMOTE_DB_HOST=$RemoteDbHost"
    "REMOTE_DB_PORT=$RemoteDbPort"
    "SYNC_FROM_DATETIME=$SyncFromDateTime"
    "SYNC_BATCH_SIZE=$BatchSize"
    "SYNC_INTERVAL_SECONDS=$IntervalSeconds"
)
$envExtra = [string]::Join("`n", $envPairs)
Invoke-Nssm set $ServiceName AppEnvironmentExtra $envExtra

if ($null -ne $existingService -and $existingService.Status -eq "Running") {
    Invoke-Nssm stop $ServiceName
    Start-Sleep -Seconds 2
}

Invoke-Nssm start $ServiceName
Write-Host "Service ishga tushdi: $ServiceName"
