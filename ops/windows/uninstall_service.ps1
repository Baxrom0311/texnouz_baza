[CmdletBinding()]
param(
    [string]$NssmExe = "nssm",

    [string]$ServiceName = "MMSBridge"
)

$ErrorActionPreference = "Stop"

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
    Start-Sleep -Seconds 2
}

Invoke-Nssm remove $ServiceName confirm
Write-Host "Service o'chirildi: $ServiceName"
