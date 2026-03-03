[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$NssmExe,

    [string]$ServiceName = "MMSBridge"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $NssmExe)) {
    throw "NSSM topilmadi: $NssmExe"
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
