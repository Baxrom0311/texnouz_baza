# Windows Production (NSSM)

Bu papkadagi scriptlar `main.py` bridge ni Windowsda production tarzda ishlatish uchun.

## 1) EXE build

PowerShell (Admin emas ham bo'ladi):

```powershell
Set-Location C:\path\to\mms
powershell -ExecutionPolicy Bypass -File .\ops\windows\build_exe.ps1 -Clean
```

Natija: `dist\mms_bridge.exe`

## 2) NSSM service install/update

Admin PowerShell:

```powershell
Set-Location C:\path\to\mms
powershell -ExecutionPolicy Bypass -File .\ops\windows\install_service.ps1 `
  -NssmExe "C:\tools\nssm\nssm.exe" `
  -RemoteDbPassword "sync_pass12345" `
  -LocalDbHost "127.0.0.1" `
  -SyncFromDateTime "2026-03-01 00:00:00"
```

Default install joyi:

- `C:\Program Files\MMSBridge\mms_bridge.exe`
- `C:\Program Files\MMSBridge\logs\mms_bridge.out.log`
- `C:\Program Files\MMSBridge\logs\mms_bridge.err.log`

Kerak bo'lsa custom papka:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\install_service.ps1 `
  -NssmExe "C:\tools\nssm\nssm.exe" `
  -InstallDir "D:\Services\MMSBridge"
```

Script idempotent:
- service bo'lmasa yaratadi,
- `dist\mms_bridge.exe` ni install papkaga ko'chiradi,
- bo'lsa config ni yangilaydi,
- oxirida qayta ishga tushiradi.

## 3) Service holatini tekshirish

```powershell
Get-Service MMSBridge
```

Loglar:
- `C:\Program Files\MMSBridge\logs\mms_bridge.out.log`
- `C:\Program Files\MMSBridge\logs\mms_bridge.err.log`

## 4) Uninstall

```powershell
Set-Location C:\path\to\mms
powershell -ExecutionPolicy Bypass -File .\ops\windows\uninstall_service.ps1 `
  -NssmExe "C:\tools\nssm\nssm.exe"
```

Install papkani ham o'chirish kerak bo'lsa:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\uninstall_service.ps1 `
  -NssmExe "C:\tools\nssm\nssm.exe" `
  -RemoveInstallDir
```

## Muhim env/config

Servicega beriladigan asosiy env:
- `LOCAL_DB_NAME`, `LOCAL_DB_USER`, `LOCAL_DB_PASSWORD`, `LOCAL_DB_HOST`, `LOCAL_DB_PORT`
- `REMOTE_DB_NAME`, `REMOTE_DB_USER`, `REMOTE_DB_PASSWORD`, `REMOTE_DB_HOST`, `REMOTE_DB_PORT`
- `SYNC_FROM_DATETIME` (`tabmaindata.DateTime >= shu qiymat`)
- `SYNC_BATCH_SIZE`, `SYNC_INTERVAL_SECONDS`

`main.py` bu qiymatlarni env'dan o'qiydi, shuning uchun har site uchun exe qayta build qilish shart emas.
