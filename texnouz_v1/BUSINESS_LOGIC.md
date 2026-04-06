# Texnouz v1 - To'liq Biznes Logika Tahlili
> Manba: pe-sieve bilan unpack qilingan `400000.Texnouz.exe` + radare2 tahlili
> Sana: 2026-04-06

---

## 1. ARXITEKTURA

```
Texnouz.exe (Delphi 7, VMProtect 2.04)
│
├── MS Access MDB (C:\Windows\System32\System32.mdb) ─ asosiy DB
├── COM Port 1 (9600 baud, 8N1) ─ Mariya protokol (TRK/gaz kolonkasi)
├── COM Port 2 ─ Shtrih printer (chek chiqarish)
├── AZSOInternet.dll / ShelfInternet.dll ─ internet sinxronizatsiya
└── Base\Shelf.dsn ─ Office DB ulanishi (sinxronizatsiya uchun)
```

**Ikki xil DB:**
- `System32.mdb` — stantsiya (AZS) ishchi DB
- `Base\Shelf.dsn` / `tabXxxOffice` — Office (bosh ofis) DB sinxronizatsiya

---

## 2. JADVALLAR VA MAQSADI

| Jadval | Maqsad | Muhim ustunlar |
|---|---|---|
| `tabOperator` | Operatorlar (login/parol) | OperatorID, AZSID, Password(10), Type |
| `tabOperatorType` | Operator rollari | TypeID, TypeName |
| `tabChange` | Smenalar (shift) | ChangeID, StartDateTime, EndDateTime, ClosedFlag, CloseType, OpenCounter, SYNC |
| `tabGasType` | Gaz turlari va narxlar | GasID, GasName, CheckName, Price, Discount1/2/3, GasMetan, MTaxTypes, Dencity |
| `tabStorage` | Sisternalar (ombor) | CisternID, GasID, Volume, SYNC |
| `tabTRK` | TRK kolonka sozlamalari | TRKID, CisternID, PistoletID, Half, HorPos, VerPos, MPort, MBaud |
| `tabLevelMeters` | Daraja o'lchagich | CisternID, LevMetType, SerialNum, LMName, ZeroOffset |
| `tabMainData` | Barcha tranzaksiyalar | 36 ta ustun (gaz, tovar, to'lov) |
| `tabMainDataHistory` | Arxiv tranzaksiyalar | tabMainData bilan bir xil (smena yopilganda ko'chiriladi) |
| `tabSummCounters` | Pistolet schetchiklari | ChangeID, PistNum, BeginCounter, EndCounter, SYNC |
| `tabGasHistory` | Gaz kiritish tarixi | ChangeID, CisternID, AddLiters, Density, Temperature, NumAuto, SYNC |
| `tabPriceHistory` | Narx o'zgarish tarixi | GasID, Price, Discount1/2/3, MTaxTypes |
| `tabPartner` | Hamkorlar/mijozlar | PartnerID, Name, Enabled |
| `tabPartnerAccount` | Hamkor hisobi (debet/kredit) | PartnerID, GasID, Debet, Credit |
| `tabPartnerInHistory` | Hamkor kirim tarixi | PartnerID, CardID, GasID, DataID, Debet, Credit |
| `tabPartnerOutHistory` | Hamkor chiqim tarixi | PartnerID, CardID, GasID, DataID, Debet, Credit |
| `tabCarPassport` | Avtomobil taloni | CarID, TalonNumber, CarNumber, CarType, BalloonNum, FirmName, EndDate, SYNC |
| `tabCardNumbers` | Smart kartalar | CardNumber, CardType, GasID, PartnerID, DiscSchema, Liters, EndDate, Sold, Enabled |
| `tabCardTypes` | Karta turlari | CTNum, CTName |
| `tabGoods` | Tovarlar (do'kon) | GoodsID, Article, Name, BarCode, Price, Discount, Divided, Taxes |
| `tabGoodsHistory` | Tovar harakati tarixi | GoodsID, Article, Amount, ChangeID |
| `tabGoodsPriceHistory` | Tovar narx tarixi | GoodsID, Article, Price, Discount |
| `tabOperation` | Operatsiya turlari | OperationID, Name |
| `tabErrors` | Xato kodlari | CodeID, ErrorName |
| `tabTaxes` | Soliqlar | TaxID, Name, Percent, TaxType |
| `tabTaxsTypes` | Soliq turlari | TTID, Name |
| `tabSchema` | Konfiguratsiya sxemalari | SchName, SchData |
| `tabVersion` | Versiya ma'lumoti | AZSID, VersionRelease, VersionMajor, VersionMinor |

**Office sinxronizatsiya uchun alohida jadvallar:**
`tabCarPassportOffice`, `tabCardNumbersOffice`, `tabGasTypeOffice`, `tabGoodsOffice`,
`tabOperatorOffice`, `tabPartnerOffice`, `tabSchemaOffice`, `tabTaxesOffice`

---

## 3. SMENA (SHIFT) BOSHQARUVI

### Smena ochish:
```sql
INSERT INTO tabChange
  (StartDateTime, EndDateTime, OperatorID, ClosedFlag, CloseType, OpenCounter, SYNC)
VALUES ('2024-01-01 08:00:00', NULL, 1, false, 0, 0, false)
```

### Smena yopish:
```sql
-- 1. tabChange ni yangilash
UPDATE tabChange SET
  EndDateTime = '2024-01-01 20:00:00',
  ClosedFlag  = true,
  CloseType   = [0=normal|1=force|...],
  SYNC        = false
WHERE ChangeID = [ID]

-- 2. tabMainData → tabMainDataHistory ko'chirish (har bir yozuv uchun)
INSERT INTO tabMainDataHistory (DataID, ChangeID, GasID, ...)
  SELECT DataID, ChangeID, GasID, ...
  FROM tabMainData WHERE ChangeID = [ID]

DELETE FROM tabMainData WHERE ChangeID = [ID]

-- 3. tabSummCounters (pistolet schetchiklari) yangilanadi
UPDATE tabSummCounters SET EndCounter = [value] WHERE ChangeID = [ID]
```

### Faol smena topish:
```sql
SELECT Max(ChangeID) AS MaxNum FROM tabChange
-- yoki
SELECT tabChange.ChangeID, StartDateTime, EndDateTime, OperatorID, ClosedFlag
FROM tabChange, tabOperator
WHERE tabChange.OperatorID = tabOperator.OperatorID
ORDER BY ChangeID
```

---

## 4. GAZ QUYISH JARAYONI (asosiy tranzaksiya)

### 4.1 Naqd pul bilan to'liq gaz quyish (pistoletli):
```sql
INSERT INTO tabMainData
  (ChangeID, GasID, GasMetan, CisternID, PartnerID, OperationID, PistoletID,
   OrderLiters, OrderMoney, Liters, MoneyCash, Price, Discount1, Discount2,
   Debet, Credit, WaterLevel, EndCode, Kbrd, OperatorID,
   CasseID, [DateTime], SYNC, CarNumber, CardNumber)
VALUES (...)
```

### 4.2 Litrni o'lchash:
- `Liters` ustuni = haqiqiy litr * 100 (masalan: 10.50 litr = 1050)
- `OrderLiters` = buyurtma qilingan litr * 100
- `OrderMoney` = buyurtma qilingan pul miqdori

### 4.3 To'lov turlari:
| Ustun | Tavsif |
|---|---|
| `MoneyCash` | Naqd pul |
| `MoneyTalon` | Talon (hamkor talon) |
| `MoneyBank` | Bank kartasi |
| `MoneyFut` | Muddatli/kredit |
| `Debet` | Hamkor debeti |
| `Credit` | Hamkor krediti |

### 4.4 Metan gaz (CNG):
- `GasMetan` = 1 bo'lsa metan gaz
- `MGasLevel` = metan gaz bosim sensori qiymati
- `Pressure` = bosim
- `Dencity` = zichlik
- `Mass` = massa

### 4.5 Smart karta bilan to'lov:
```sql
INSERT INTO tabMainData
  (ChangeID, GasID, GasMetan, PartnerID, OperationID,
   MoneyCash, MoneyBank, MoneyTalon, MoneyFut, Debet, EndCode,
   OperatorID, CasseID, [DateTime], SYNC, CardNumber)
VALUES (...)
```

### 4.6 Hamkor (partner) debeti bilan:
```sql
-- tabMainData ga yozish (Debet = yechilgan litrlar * 100)
-- tabPartnerOutHistory ga qo'shish
INSERT INTO tabPartnerOutHistory
  (PartnerID, CardID, GasID, DataID, ChangeID, Debet, Credit, OperatorID, [DateTime])
VALUES (...)

-- tabPartnerAccount ni yangilash
UPDATE tabPartnerAccount SET Debet = Debet + [amount]
WHERE PartnerID = [ID]
```

---

## 5. TOVAR SOTISH (do'kon rejimi)

### Naqd pul bilan tovar sotish:
```sql
INSERT INTO tabMainData
  (ChangeID, PartnerID, OperationID, Count, Article, MoneyCash,
   Price, Discount1, Discount2, OperatorID, [DateTime], CheckID, EndCode, SYNC)
VALUES (...)
```

### Bank kartasi bilan tovar sotish:
```sql
INSERT INTO tabMainData
  (ChangeID, PartnerID, OperationID, Count, Article, MoneyBank,
   Price, Discount1, Discount2, OperatorID, [DateTime], CheckID, EndCode, SYNC)
VALUES (...)
```

### Tovar hisobi:
```sql
SELECT Article, Sum(Count) AS SCount
FROM tabMainData
WHERE (OperationID = [ID1]) OR (OperationID = [ID2])
GROUP BY Article
```

---

## 6. OMBOR (SISTERNA) BOSHQARUVI

### Gaz kiritish (tanker kelganda):
```sql
INSERT INTO tabGasHistory
  (ChangeID, CisternID, StartGasLevel, StartWaterLevel, StartLiters,
   EndGasLevel, EndWaterLevel, EndLiters, AddLiters, [Date],
   OperatorID, Density, Temperature, NumAuto, ExpeditorName,
   SalerName, NumDocum, DateDocum, GasMetan, SYNC)
VALUES (...)
```
- `AddLiters` = kiritilgan litr * 100

### Sisterna hajmini yangilash:
```sql
UPDATE tabStorage SET Volume = [yangi_hajm]
WHERE CisternID = [ID]
```

### Sisterna qoldig'ini hisoblash:
```sql
SELECT Sum(WaterLevel) as SWaterLevel, Sum(Liters)/100 as SLiters
FROM tabMainData
WHERE CisternID = [ID]
```

---

## 7. PISTOLET SCHETCHIKLARI

### Schetchik boshlanishi (smena ochilganda):
```sql
SELECT BeginCounter, EndCounter FROM tabSummCounters WHERE ChangeID = [ID]
```

### Schetchik yangilanishi (smena davomida):
```sql
UPDATE tabSummCounters SET EndCounter = [value]
WHERE ChangeID = [ID] AND PistNum = [pistolet_num]
```

### Smena yopilganda pistolet qiymat saqlash:
- `BeginCounter` = smena boshidagi schetchik ko'rsatgich
- `EndCounter` = smena oxiridagi schetchik ko'rsatgich
- Farq = smena davomida quyilgan litrlar

---

## 8. HAMKOR HISOBI

### Hamkor debet/kredit:
```sql
SELECT Debet as SDeebt, Credit as SCredit
FROM tabPartnerAccount
WHERE PartnerID = [ID]
```

### Debet qo'shish (gaz berilganda):
```sql
UPDATE tabPartnerAccount SET Debet = Debet + [liters]
WHERE PartnerID = [ID]

-- Yoki to'liq o'zgartirish:
UPDATE tabPartnerAccount SET Debet = [new_value]
WHERE PartnerID = [ID]
```

### Hamkor to'lovi (pul kiritilganda):
```sql
-- tabPartnerInHistory ga yozish
INSERT INTO tabPartnerInHistory
  (PartnerID, GasID, DataID, ChangeID, Debet, Credit, OperatorID, [DateTime])
VALUES (...)

-- tabMainData ga yozish (kredit operatsiya)
INSERT INTO tabMainData
  (ChangeID, OperationID, MoneyCash, PartnerID, GasID, GasMetan,
   EndCode, OperatorID, [DateTime], SYNC)
VALUES (...)
```

---

## 9. AVTOMOBIL TALON TIZIMI

### Talon tekshirish:
```sql
SELECT CarID, CarNumber, CarType FROM tabCarPassport
WHERE CarNumber = '[raqam]'
```

### Yangi talon yaratish:
```sql
INSERT INTO tabCarPassport
  (TalonNumber, CarNumber, CarType, BalloonNum, FirmName, EndDate, OperatorID, SYNC)
VALUES (...)
```

### Talon bilan gaz quyish:
- `MoneyTalon` ustuniga qiymat yoziladi
- `CarNumber` ustuniga avtomobil raqami yoziladi

---

## 10. SMART KARTA TIZIMI

### Karta yaratish:
```sql
INSERT INTO tabCardNumbers
  (CardNumber, CardType, PartnerID, DiscSchema, Liters, GasID,
   EndDate, [Date], OperatorID, Sold, Enabled)
VALUES (...)
```

### Karta bilan to'lov:
- `CardNumber` ustuniga karta raqami yoziladi
- `DiscSchema` = chegirma sxemasi (discount schema ID)
- `Liters` = karta limiti (litr)

---

## 11. SOLIQ TIZIMI

### Soliq ma'lumotlari:
- `MTaxTypes` (TEXT 8) = 8 ta soliq turi uchun bitmask string (masalan: `'--------'`)
- `tabTaxes`: TaxID, Name (10 char), Percent, TaxType
- `tabTaxsTypes`: TTID, Name
- `Taxes` (TEXT 8) = tovar soliq kodi

---

## 12. CHEK (RECEIPT) TIZIMI

### Chek raqami:
```sql
SELECT Max(CheckID) as MCheckID FROM tabMainData
-- Yangi CheckID = Max + 1
```

### Chek printerlash:
- **Shtrih protokol** - COM port orqali Shtrih kassa printerga
- `TCasseShtrih::Sale` - oddiy tovar sotish
- `TCasseShtrih::PrintCheck` - chek chiqarish
- `TCasseShtrih::ZReport` - Z-hisobot (smena oxiri)
- `CasseID` = kassa qurilmasi ID

---

## 13. INTERNET SINXRONIZATSIYA

### `tabSchema` - konfiguratsiya:
```sql
INSERT INTO tabSchema (SchName, SchData) VALUES ('[kalit]', '[qiymat]')
UPDATE tabSchema SET SchName = '[kalit]', SchData = '[qiymat]'
SELECT SchData FROM tabSchema WHERE SchName = '[kalit]'
```

### Sinxronizatsiya bayroqlari:
- `SYNC = false` → yangi/o'zgargan yozuv, office ga yuborilmagan
- `SYNC = true` → sinxronlangan

### SyncMask - qaysi maydonlar sinx:
- `SyncMask0..SyncMask4` - 5 ta sinxronizatsiya turi maski

### Office DB (Shelf.dsn):
```
;DefaultDir=Base;Driver={Driver do Microsoft Access (*.mdb)};
DriverId=25;FIL=MS Access;FILEDSN=Base\Shelf.dsn;
MaxBufferSize=2048;MaxScanRows=8;PageTimeout=5;
SafeTransactions=0;UID=admin;
```

### `AZSOInternet.dll` / `ShelfInternet.dll`:
- `TShelfGas` - benzin sinxronizatsiyasi
- `TShelfGasLow` - kam yoqilg'i signal
- `TShelfMetan` - metan sinxronizatsiyasi
- `ShelfAZSMutex` - thread lock

---

## 14. MARIYA PROTOKOL (TRK/Kolonka)

### Konfiguratsiya (Texnouz.INI):
```ini
[COMM]
Port=COM1
BaudRate=9600
DataBits=8
Parity=None
```

### TRK jadval:
```
TRKID, CisternID, PistoletID, Half
HorPos, VerPos (ekranda joylashuv)
MPort, MBaud (COM port sozlamasi)
MUseCnt (schetchik ishlatish)
MUseAvaP (bosimni o'lchash)
MImpuls, MMaxCnt (impuls sozlamasi)
```

### TRK frames (UI):
- `TframeTRK` - har bir kolonka uchun frame
- `TframePistolet` - pistolet frame
- `btnStartClick` - gaz berishni boshlash
- `btnStopClick` - gaz berishni to'xtatish
- `btnFullClick` - to'liq tank

---

## 15. HISOBOTLAR

### Hisobot fayllari: `Reports\*.rep`
- HTMLReport orqali hosil qilinadi
- Smena hisoboti, Kunlik hisobot, Oylik hisobot

### Asosiy hisoblash so'rovlari:
```sql
-- Smena davomida naqd pul jami
SELECT Sum(MoneyCash) as SMoney FROM tabMainData WHERE ChangeID = [ID]

-- Smena davomida bank jami
SELECT Sum(MoneyBank) as SMoney FROM tabMainData WHERE ChangeID = [ID]

-- Smena davomida quyilgan litr
SELECT -Sum(Liters)/100 as SLiters FROM tabMainData WHERE ChangeID = [ID]

-- Pistolet uchun litr (manfiy chunki litr chiqim)
SELECT -Sum(Liters) AS SNCLiters FROM tabMainData WHERE PistoletID = [ID]

-- Gaz turi bo'yicha litr
SELECT -Sum(Liters)/100 as SLiters FROM tabMainData WHERE GasID = [ID]
```

### Tarix tozalash (eski yozuvlarni o'chirish):
```sql
DELETE FROM tabMainDataHistory WHERE [DateTime] <= #[date]#
DELETE FROM tabGasHistory WHERE [Date] <= #[date]#
DELETE FROM tabPriceHistory WHERE [DateTime] <= #[date]#
DELETE FROM tabChange WHERE [EndDateTime] <= #[date]#
DELETE FROM tabSummCounters WHERE [EndDateTime] <= #[date]#
DELETE FROM tabPartnerInHistory WHERE [DateTime] <= #[date]#
DELETE FROM tabPartnerOutHistory WHERE [DateTime] <= #[date]#
DELETE FROM tabGoodsHistory WHERE [DateTime] <= #[date]#
DELETE FROM tabGoodsPriceHistory WHERE [DateTime] <= #[date]#
```

---

## 16. VERSIYA VA IDENTIFIKATSIYA

```sql
-- Stantsiya ID
UPDATE tabVersion SET AZSID = [id]
SELECT * FROM tabVersion

-- Versiya upgrade
UPDATE tabVersion SET VersionRelease = 0, VersionMajor = 2, VersionMinor = 0 WHERE Cnt = 1
UPDATE tabVersion SET VersionRelease = 1 WHERE Cnt = 1  -- patch 1
UPDATE tabVersion SET VersionRelease = 2 WHERE Cnt = 1  -- patch 2
UPDATE tabVersion SET VersionRelease = 3 WHERE Cnt = 1  -- patch 3
UPDATE tabVersion SET VersionRelease = 4 WHERE Cnt = 1  -- patch 4
```

### AZSID:
- Har bir AZS stantsiyasi o'z AZSID ga ega
- `tabOperator.AZSID` - operator qaysi stantsiyada
- `tabVersion.AZSID` - stantsiya umumiy ID

---

## 17. MODULLAR VA FORMALAR

| Modul | Vazifa |
|---|---|
| `Kernel` | Asosiy biznes logika (InitDataBase, InitHard, InitApplication) |
| `Mainform` | Asosiy oyna |
| `Getgasform` | Gaz quyish formasi |
| `Getgasformadd` | Qo'shimcha gaz formasi |
| `Casseform` | Kassa formasi |
| `Casseclass` | Kassa logikasi (TCasseShtrih) |
| `Cassethr` | Kassa threadi |
| `Storageform` | Ombor boshqaruvi |
| `Operatorform` | Operator boshqaruvi |
| `Partnerform` | Hamkor boshqaruvi |
| `Partnerlitersform` | Hamkor litr hisobi |
| `Trkform` / `Trkframe` | TRK boshqaruvi |
| `Pistoletframe` | Pistolet frame |
| `Gastypeform` | Gaz turi boshqaruvi |
| `Cardcreateform` | Karta yaratish |
| `Cardactivateform` | Karta aktivlashtirish |
| `Cardlitersform` | Karta litr hisob |
| `Cartalonform` | Talon tizimi |
| `Discountschform` | Chegirma sxemasi |
| `Priceform` / `Setpriceform` | Narx boshqaruvi |
| `Goodsform` / `Shopform` | Tovar boshqaruvi |
| `Mariyaclass` / `Mariyaprotocol` | Mariya qurilma protokoli |
| `Shtrihclass` / `Shtrihprotocol` | Shtrih printer protokoli |
| `Dbsyncronization` | DB sinxronizatsiya |
| `Internetprotocol` / `Shelfclass` | Internet |
| `Htmlreport` | HTML hisobotlar |
| `Taxesform` | Soliq boshqaruvi |
| `Levelmeter` | Daraja o'lchagich |
| `Readerclass` | Karta o'quvchi |
| `Blowfish` / `Md5` | Shifrlash (parol uchun) |

---

## 18. MUHIM KONSTANTALAR

### OperationID turlari (tabOperation):
> To'liq ro'yxat: `SELECT * FROM tabOperation` bilan ko'rish
- OperationID = 4,5 → naqd chiqim (gaz sotish) ← .rep fayllaridan
- OperationID = 6,7 → naqd kirim (partner to'lov)
- Tovar sotish uchun alohida OperationID lar mavjud

### EndCode turlari:
- 0 = muvaffaqiyatli tugash
- Boshqa qiymatlar = xato kodlari (tabErrors bilan bog'liq)

### CloseType (smena yopish turi):
- tabChange.CloseType - smena qanday yopilgani

### Version:
- VersionMajor = 2, VersionMinor = 0
- VersionRelease = 0..4 (patch)
