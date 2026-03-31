Set-Location C:\mms

powershell -ExecutionPolicy Bypass -File .\ops\windows\install_service.ps1 `
  -NssmExe "C:\tools\nssm\nssm.exe" `
  -LocalDbName "texnouz_copy" `
  -LocalDbUser "baxrom" `
  -LocalDbPassword "SIZNING_LOCAL_DB_PAROLINGIZ" `
  -LocalDbHost "127.0.0.1" `
  -LocalDbPort 5432 `
  -RemoteDbName "mms_localhost" `
  -RemoteDbUser "sync_user1" `
  -RemoteDbPassword "SIZNING_REMOTE_DB_PAROLINGIZ" `
  -RemoteDbHost "3.122.18.70" `
  -RemoteDbPort 5432 `
  -SyncFromDateTime "2026-03-01 00:00:00" `
  -BatchSize 1000 `
  -IntervalSeconds 10


Get-Service MMSBridge

