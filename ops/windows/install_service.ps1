[CmdletBinding()]
param(
    [string]$NssmExe = "nssm",

    [string]$ServiceName = "MMSBridge",
    [string]$ProjectRoot = "",
    [string]$InstallDir = "",
    [string]$AppPath = "",
    [string]$AppParameters = $null,
    [string]$LogsDir = "",

    [string]$LocalDbName = "texnouz",
    [string]$LocalDbUser = "root",
    [string]$LocalDbPassword = "qazwsxedc1234",
    [string]$LocalDbHost = "127.0.0.1",
    [int]$LocalDbPort = 5432,

    [string]$RemoteDbName = "mms_localhost",
    [string]$RemoteDbUser = "sync_user1",
    [string]$RemoteDbPassword = "sync_pass12345",
    [string]$RemoteDbHost = "3.122.18.70",
    [int]$RemoteDbPort = 5432,

    [string]$SyncFromDateTime = "2026-03-01 00:00:00",
    [int]$BatchSize = 1000,
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"

function Get-DefaultInstallDir {
    $programFiles = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles)
    if ([string]::IsNullOrWhiteSpace($programFiles)) {
        throw "Program Files papkasi aniqlanmadi."
    }
    return Join-Path $programFiles $ServiceName
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $scriptDir = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($scriptDir) -and $PSCommandPath) {
        $scriptDir = Split-Path -Parent $PSCommandPath
    }
    if ([string]::IsNullOrWhiteSpace($scriptDir) -and $MyInvocation.MyCommand.Path) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    if ([string]::IsNullOrWhiteSpace($scriptDir)) {
        $scriptDir = (Get-Location).Path
    }
    $ProjectRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
}

if (Test-Path $NssmExe) {
    $NssmExe = (Resolve-Path $NssmExe).Path
}
else {
    $nssmCmd = Get-Command $NssmExe -ErrorAction SilentlyContinue
    if ($null -eq $nssmCmd) {
        throw "NSSM topilmadi. Path yoki command bering: $NssmExe"
    }
    $NssmExe = $nssmCmd.Source
}

function Invoke-Nssm {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]]$Args)
    & $NssmExe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "NSSM xatosi: $($Args -join ' ')"
    }
}

$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -ne $existingService -and $existingService.Status -eq "Running") {
    Invoke-Nssm stop $ServiceName
    $existingService.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(30))
}

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = Get-DefaultInstallDir
}
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$InstallDir = (Resolve-Path $InstallDir).Path

if ([string]::IsNullOrWhiteSpace($AppPath)) {
    $AppPath = Join-Path $ProjectRoot "dist\mms_bridge.exe"
}
if (-not (Test-Path $AppPath)) {
    throw "Exe topilmadi: $AppPath"
}
$AppPath = (Resolve-Path $AppPath).Path

$installedAppPath = Join-Path $InstallDir ([System.IO.Path]::GetFileName($AppPath))
if (-not [System.String]::Equals($AppPath, $installedAppPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    Copy-Item -Path $AppPath -Destination $installedAppPath -Force
}
$AppPath = $installedAppPath

if ([string]::IsNullOrWhiteSpace($LogsDir)) {
    $LogsDir = Join-Path $InstallDir "logs"
}
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
$LogsDir = (Resolve-Path $LogsDir).Path

$stdoutPath = Join-Path $LogsDir "mms_bridge.out.log"
$stderrPath = Join-Path $LogsDir "mms_bridge.err.log"

if ($null -eq $existingService) {
    Invoke-Nssm install $ServiceName $AppPath
}

Invoke-Nssm set $ServiceName Application $AppPath
Invoke-Nssm set $ServiceName AppDirectory $InstallDir
if (-not [string]::IsNullOrWhiteSpace($AppParameters)) {
    Invoke-Nssm set $ServiceName AppParameters $AppParameters
}
else {
    Invoke-Nssm reset $ServiceName AppParameters
}
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

Invoke-Nssm start $ServiceName
Write-Host "Service ishga tushdi: $ServiceName"
Write-Host "Install papkasi: $InstallDir"
Write-Host "Log papkasi: $LogsDir"
