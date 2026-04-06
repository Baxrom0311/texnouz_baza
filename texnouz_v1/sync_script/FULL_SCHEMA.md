# Texnouz v1 - To'liq Database Schema (Reverse Engineering natijasi)

> **Manba**: `Texnouz.exe` reverse engineering + `.rep` report fayllar tahlili
> **Texnologiya**: Delphi 5/6/7 + MS Access (MDB) + VMProtect himoya

---

## Topilgan barcha jadvallar

| Jadval | Tavsif |
|---|---|
| `tabMainData` | Asosiy tranzaksiya (yoqilg'i quyish) |
| `tabMainDataHistory` | Arxivlangan tranzaksiyalar (smena yopilgandan so'ng) |
| `tabChange` | Smenalar (shifts) |
| `tabOperator` | Operatorlar |
| `tabOperatorType` | Operator rollari/turlari |
| `tabPartner` | Hamkorlar/mijozlar |
| `tabCarPassport` | Avtomobil pasporti (talon) |
| `tabGasType` | Gaz turlari va narxlari |
| `tabGasHistory` | Omborga gaz kiritish tarixi |
| `tabStorage` | Ombor (sisternalar) joriy holati |
| `tabPriceHistory` | Narx o'zgarish tarixi |
| `tabOperation` | Operatsiya turlari |
| `tabErrors` | Xato kodlari |
| `tabSummCounters` | Yig'ma schetchiklar (pistolet oborotlari) |

---

## Batafsil Schema

### tabMainData - Asosiy tranzaksiyalar
```sql
DataID       INTEGER  -- PK, tranzaksiya ID
ChangeID     INTEGER  -- FK -> tabChange.ChangeID
PistoletID   INTEGER  -- FK -> pistolet raqami
OperatorID   INTEGER  -- FK -> tabOperator.OperatorID
PartnerID    INTEGER  -- FK -> tabPartner.PartnerID
OperationID  INTEGER  -- FK -> tabOperation.OperationID
CisternID    INTEGER  -- FK -> tabStorage.CisternID
GasID        INTEGER  -- FK -> tabGasType.GasID
GasMetan     BOOLEAN  -- Metan gaz bayrog'i (0=yo'q, 1=ha)
Liters       INTEGER  -- Quyilgan litr * 100 (e.g. 100 = 1.00 litr)
OrderLiters  INTEGER  -- Buyurtma qilingan litr * 100
OrderMoney   FLOAT    -- Buyurtma puli
Price        INTEGER  -- Narx
Discount     FLOAT    -- Chegirma
Debet        FLOAT    -- Debet (qarz)
Credit       FLOAT    -- Kredit
MoneyCash    FLOAT    -- Naqd to'lov
MoneyBank    FLOAT    -- Bank to'lov
WaterLevel   INTEGER  -- Suvlik darajasi
MGasLevel    FLOAT    -- Gaz darajasi (metan sensori)
MWaterLevel  FLOAT    -- Suv darajasi (metan sensori)
DateTime     DATETIME -- Tranzaksiya vaqti
EndCode      INTEGER  -- Tugash kodi (normal/xato)
Kbrd         TEXT     -- Klaviatura kiritimlari
CarNumber    TEXT     -- Avtomobil raqami (talon uchun)
SYNC         BOOLEAN  -- Sinxronizatsiya bayrog'i
```

### tabMainDataHistory - Arxiv tranzaksiyalar
```sql
-- tabMainData bilan bir xil tuzilma, smena yopilganda ma'lumotlar shu yerga ko'chiriladi
DataID, ChangeID, PistoletID, OperatorID, PartnerID, OperationID, CisternID, GasID,
GasMetan, Liters, OrderLiters, OrderMoney, Price, Discount, Debet, Credit,
MoneyCash, MoneyBank, WaterLevel, MGasLevel, MWaterLevel, DateTime, EndCode, Kbrd
```

### tabChange - Smenalar
```sql
ChangeID      INTEGER  -- PK, smena ID
OperatorID    INTEGER  -- FK -> tabOperator.OperatorID
StartDateTime DATETIME -- Smena boshlanish vaqti
EndDateTime   DATETIME -- Smena tugash vaqti (NULL = ochiq)
-- closed flag (inferred from EndDateTime)
```

### tabOperator - Operatorlar
```sql
OperatorID  INTEGER  -- PK
Name        TEXT     -- Ism-familiya
Address     TEXT     -- Manzil
Phone       TEXT     -- Telefon raqami
Date        DATETIME -- Ro'yxatga olingan sana
Type        INTEGER  -- FK -> tabOperatorType.TypeID
```

### tabOperatorType - Operator turlari
```sql
TypeID    INTEGER  -- PK
TypeName  TEXT     -- Tur nomi (masalan: Admin, Operator, Kassir)
```

### tabPartner - Hamkorlar/Mijozlar
```sql
PartnerID  INTEGER  -- PK
Name       TEXT     -- Hamkor/mijoz nomi
```

### tabCarPassport - Avtomobil pasporti (Talon tizimi)
```sql
CarNumber   TEXT     -- Avtomobil raqami (PK yoki UK)
TalonNumber TEXT     -- Talon raqami
OperatorID  INTEGER  -- FK -> tabOperator.OperatorID
CarType     TEXT     -- Avtomobil turi
BalloonNum  TEXT     -- Ballon raqami
FirmName    TEXT     -- Firma nomi
EndDate     DATETIME -- Talon tugash muddati
```

### tabGasType - Gaz turlari
```sql
GasID      INTEGER  -- PK
CheckName  TEXT     -- Chek/hisobot uchun nom
Price      INTEGER  -- Narx (tiyin)
Dencity    INTEGER  -- Zichlik
IsMetan    BOOLEAN  -- Metan gaz bayrog'i
```

### tabStorage - Ombor (Sisternalar)
```sql
CisternID  INTEGER  -- PK
GasID      INTEGER  -- FK -> tabGasType.GasID
Volume     FLOAT    -- Joriy hajm (litr)
```

### tabGasHistory - Gaz kiritish tarixi
```sql
ChangeID   INTEGER  -- FK -> tabChange.ChangeID
CisternID  INTEGER  -- FK -> tabStorage.CisternID
AddLiters  INTEGER  -- Kiritilgan litr * 100
GasMetan   BOOLEAN  -- Metan bayrog'i
Date       DATETIME -- Kiritish vaqti
OperatorID INTEGER  -- FK -> tabOperator.OperatorID
```

### tabPriceHistory - Narx tarixi
```sql
GasID      INTEGER  -- FK -> tabGasType.GasID
Price      INTEGER  -- Yangi narx
Discount   FLOAT    -- Chegirma
DateTime   DATETIME -- O'zgarish vaqti
OperatorID INTEGER  -- FK -> tabOperator.OperatorID
```

### tabOperation - Operatsiya turlari
```sql
OperationID  INTEGER  -- PK
Name         TEXT     -- Operatsiya nomi
-- OperationID = 4,5 = naqd chiqim; 6,7 = naqd kirim (inferred from SQL)
```

### tabErrors - Xato kodlari
```sql
CodeID     INTEGER  -- PK
ErrorName  TEXT     -- Xato tavsifi
```

### tabSummCounters - Yig'ma schetchiklar
```sql
ChangeID      INTEGER  -- FK -> tabChange.ChangeID
PistNum       INTEGER  -- Pistolet raqami
BeginCounter  BIGINT   -- Boshlang'ich schetchik
EndCounter    BIGINT   -- Yakuniy schetchik
-- DiffLiters = EndCounter - BeginCounter (computed)
StartDateTime DATETIME -- (from tabChange)
EndDateTime   DATETIME -- (from tabChange)
```

---

## Asosiy biznes logika

### 1. Gas quyish jarayoni
```
Operator login → Smena ochiladi (tabChange)
↓
Avtomobil keladi → CarNumber kiritiladi
↓
Pistolet tanladi → GasType aniqlanadi
↓
Miqdor/pul buyurtma (OrderLiters yoki OrderMoney)
↓
Qurilma (Mariya/TRK) orqali gaz quyiladi
↓
Amaliy litr + Pressure + WaterLevel yoziladi
↓
To'lov (MoneyCash/MoneyBank) qabul qilinadi
↓
tabMainData ga INSERT qilinadi
↓
Chek chiqariladi (Shtrih printer)
```

### 2. Smena boshqaruvi
```
Smena ochish: tabChange INSERT (StartDateTime, OperatorID)
Smena davomida: tabMainData ga tranzaksiyalar
Smena yopish:
  - tabChange.EndDateTime = NOW()
  - tabMainData → tabMainDataHistory (ko'chirish)
  - tabSummCounters yangilanadi
  - Yig'ma hisobot chiqariladi
```

### 3. Qurilma protokollari
- **Mariya Protocol**: COM port orqali gaz schetchiki/kolonnasi boshqaruvi
- **Shtrih Protocol**: COM port orqali chek printer
- **AZSO Internet / Shelf Internet**: DLL orqali internet ulanish

---

## Delphi Units/Forms ro'yxati

| Unit | Vazifa |
|---|---|
| `Mainform` | Asosiy oyna |
| `Getgasform` / `Getgasformadd` | Gaz quyish formasi |
| `Storageform` | Ombor boshqaruvi |
| `Casseform` | Kassir |
| `Operatorform` | Operator boshqaruvi |
| `Partnerform` / `Partnerlitersform` | Hamkor boshqaruvi |
| `Trkform` / `Trkframe` / `Pistoletframe` | TRK va pistolet |
| `Cardcreateform` / `Cardactivateform` / `Cardlitersform` | Smart karta |
| `Cartalonform` | Avtomobil talon |
| `Discountschform` | Chegirma sxemasi |
| `Priceform` / `Setpriceform` / `Shoppriceform` | Narx boshqaruvi |
| `Goodsform` / `Getgoodsform` / `Shopform` | Tovarlar (do'kon) |
| `Logform` | Jurnal/log |
| `Settingsform` / `Comportsettings` | Sozlamalar |
| `Mariyasettingsform` / `Mariyaprotocol` / `Mariyaclass` | Mariya qurilmasi |
| `Shtrihsettingsform` / `Shtrihprotocol` / `Shtrihclass` | Shtrih printer |
| `Registrationform` | Ro'yxatdan o'tish |
| `Taxesform` | Soliq |
| `Dbsyncronization` | DB sinxronizatsiya |
| `Internetprotocol` / `Shelfclass` | Internet protokol |
| `Kernel` | Asosiy logika |
| `Checkclass` / `Checkform` | Chek |
| `Casseclass` / `Cassethr` | Kassa threadi |
| `Levelmeter` | Darajameter |
| `Readerclass` | Karta o'quvchi |
| `Deviceclass` | Qurilma klasslar |
| `Blowfish` / `Md5` / `Sparkeywrapper` | Shifrlash |
| `Commonfunctions` | Umumiy funksiyalar |
| `Datatypes` | Ma'lumot turlari |
| `Listclasses` | Ro'yxat klasslari |
| `Baseclasses` | Asosiy klasslar |
| `Htmlreport` | HTML hisobotlar |
| `Formhistory` | Tarix formasi |
