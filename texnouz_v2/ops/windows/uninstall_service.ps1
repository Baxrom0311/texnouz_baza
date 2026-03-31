[CmdletBinding()]
param(
    [string]$NssmExe = "nssm",

    [string]$ServiceName = "MMSBridge",
    [string]$InstallDir = "",
    [switch]$RemoveInstallDir
)

$ErrorActionPreference = "Stop"

function Get-DefaultInstallDir {
    $programFiles = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles)
    if ([string]::IsNullOrWhiteSpace($programFiles)) {
        throw "Program Files papkasi aniqlanmadi."
    }
    return Join-Path $programFiles $ServiceName
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

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -eq $service) {
    Write-Host "Service topilmadi: $ServiceName"
    exit 0
}

if ($service.Status -eq "Running") {
    Invoke-Nssm stop $ServiceName
    $service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(30))
}

Invoke-Nssm remove $ServiceName confirm
Write-Host "Service o'chirildi: $ServiceName"

if ($RemoveInstallDir) {
    if ([string]::IsNullOrWhiteSpace($InstallDir)) {
        $InstallDir = Get-DefaultInstallDir
    }
    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Host "Install papkasi o'chirildi: $InstallDir"
    }
}
