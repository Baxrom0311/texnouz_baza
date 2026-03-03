[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

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

$venvPath = Join-Path $ProjectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if ($Clean) {
    $buildDir = Join-Path $ProjectRoot "build"
    $distDir = Join-Path $ProjectRoot "dist"
    if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
    if (Test-Path $distDir) { Remove-Item -Recurse -Force $distDir }
}

if (-not (Test-Path $venvPython)) {
    py -3 -m venv $venvPath
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip update xatosi." }

& $venvPython -m pip install --upgrade psycopg2-binary pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Dependency install xatosi." }

Push-Location $ProjectRoot
try {
    & $venvPython -m PyInstaller --onefile --name mms_bridge main.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build xatosi." }
}
finally {
    Pop-Location
}

$exePath = Join-Path $ProjectRoot "dist\mms_bridge.exe"
Write-Host "Build tayyor: $exePath"
