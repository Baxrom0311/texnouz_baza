# texnouz_copy Database Analysis

## 1) Umumiy ma'lumot

Bu repository ichidagi backup fayllar PostgreSQL bazasiga tegishli:

- `texnouz_copy.dump` (PostgreSQL custom dump)
- `texnouz_copy.sql` (plain SQL dump)

Joriy tahlil quyidagi holatga asoslangan:

- DB nomi: `texnouz_copy`
- Restore qilingan sana: 2026-02-28
- PostgreSQL client/server: `17.x` (local)
- Dumpdan olingan asl ma'lumot:
  - Dump boshlangan vaqt: `2026-02-22 14:49:39`
  - Source DB version: `10.5`
  - Dump tool version: `17.6`
- Joriy DB hajmi: `51 MB`
- `public` schemadagi jadvallar soni: `8`

## 2) Schema qisqacha ko'rinishi

| Jadval | Rows (exact) | Hajm | Asosiy vazifa (inferred) |
|---|---:|---:|---|
| `tabmaindata` | 250381 | 43 MB | Asosiy tranzaksiya/sotuv yozuvlari |
| `tabchange` | 829 | 128 kB | Smena (ochilish-yopilish) tarixlari |
| `tabtrk` | 10 | 24 kB | TRK/pistolet mapping konfiguratsiyasi |
| `tabgastype` | 3 | 24 kB | Gaz turlari va narx/density sozlamalari |
| `taboperator` | 4 | 56 kB | Operator foydalanuvchilari |
| `taboperatortype` | 7 | 24 kB | Operator rollari (type dictionary) |
| `tabconfig` | 13 | 24 kB | Sistem konfiguratsiya kalit-qiymatlari |
| `tabsummcounter` | 0 | 8192 bytes | Summ counter agregat jadvali (hozir bo'sh) |

## 3) Bog'lanishlar (ER) va Diagramma

Muhim fakt: bazada **physical foreign key** constraintlar aniqlanmagan (`0 ta FK`).
Shunga qaramay, ustun nomlari va ma'lumotlar mosligidan kelib chiqib quyidagi bog'lanishlar ishlatiladi (inferred):

- `taboperator.Type -> taboperatortype.TypeID`
- `tabchange.OperatorID -> taboperator.OperatorID`
- `tabmaindata.ChangeID -> tabchange.ChangeID`
- `tabmaindata.OperatorID -> taboperator.OperatorID`
- `tabmaindata.PistoletID -> tabtrk.PistoletID`
- `tabsummcounter.ChangeID -> tabchange.ChangeID` (jadval bo'sh, inferred)
- `tabsummcounter.PisNum -> tabtrk.PistoletID` (jadval bo'sh, inferred)
- `tabgastype.OperatorID -> taboperator.OperatorID` (amalda qiymatlar `0`)

Referential tekshiruv (inferred linklar bo'yicha) natija:

- `tabmaindata.ChangeID` orphan: `0`
- `tabmaindata.OperatorID` orphan: `0`
- `tabchange.OperatorID` orphan: `0`
- `taboperator.Type` orphan: `0`

### Mermaid ER diagram

```mermaid
erDiagram
    TABOPERATORTYPE ||--o{ TABOPERATOR : "TypeID <- Type"
    TABOPERATOR ||--o{ TABCHANGE : "OperatorID"
    TABCHANGE ||--o{ TABMAINDATA : "ChangeID"
    TABOPERATOR ||--o{ TABMAINDATA : "OperatorID"
    TABTRK ||--o{ TABMAINDATA : "PistoletID"
    TABCHANGE ||--o{ TABSUMMCOUNTER : "ChangeID (inferred)"
    TABTRK ||--o{ TABSUMMCOUNTER : "PisNum (inferred)"
    TABOPERATOR ||--o{ TABGASTYPE : "OperatorID (optional)"

    TABCONFIG {
      bigint id PK
      varchar key
      varchar val
    }

    TABOPERATORTYPE {
      bigint TypeID PK
      varchar TypeName
    }

    TABOPERATOR {
      bigint OperatorID PK
      varchar Name PK
      varchar Password UQ
      int Type
    }

    TABCHANGE {
      bigint ChangeID PK
      timestamp StartDateTime
      timestamp EndDateTime
      int OperatorID
      boolean ClosedFlag
    }

    TABTRK {
      bigint Index PK
      int TRKID
      int PistoletID
      int Half
    }

    TABGASTYPE {
      bigint Num PK
      varchar GasName
      int Price
      int Dencity
      boolean IsMetan
      int OperatorID
    }

    TABMAINDATA {
      bigint DataID PK
      int ChangeID
      int PistoletID
      int OperatorID
      int Liters
      timestamp DateTime
      boolean SYNC
    }

    TABSUMMCOUNTER {
      bigint DataID PK
      int ChangeID
      int PisNum
      timestamp EndDateTime
      bigint BeginCounter
      bigint EndCounter
      boolean SYNC
    }
```

## 4) Data profiling (amaldagi ma'lumot)

### Vaqt oralig'i

- `tabmaindata.DateTime`: `2024-07-17 18:36:31.441` -> `2026-02-22 14:37:16.085`
- `tabchange.StartDateTime`: `2024-07-17 18:14:06.466` -> `2026-02-22 07:25:45.624`

### Asosiy agregatlar (`tabmaindata`)

- Jami yozuv: `250381`
- Unique `ChangeID`: `826`
- Unique `OperatorID`: `3`
- Unique `PistoletID`: `10`
- Jami litr (`Liters` summasi): `537119685`
- Jami to'lov komponentlari (`MoneyCash + MoneyPlastik + MoneyBank + MoneyTalon`): `21509441320.00`
- O'rtacha `Price`: `4055.51`

### Smena holati (`tabchange`)

- `ClosedFlag = true`: `828`
- `ClosedFlag = false`: `1`

### TRK/Pistolet konfiguratsiyasi

`tabtrk`da 10 ta mapping bor, barchasi `TRKID=13`, `portName='COM4'`, `PistoletID`lar:
`10, 15, 20, 25, 30, 35, 40, 45, 50, 55`

### Gaz turlari (`tabgastype`)

| Num | GasName | Price | Dencity | IsMetan | OperatorID |
|---:|---|---:|---:|---|---:|
| 2 | `+` | 4500 | 0 | false | 0 |
| 3 | `+` | 4500 | 0 | false | 0 |
| 13 | `MT2` | 5200 | 685 | true | 0 |

### Operator rollari (`taboperatortype`)

`1: Не работает`, `2: Администратор`, `3: Оператор`, `4: Настройщик`,
`5: Экономист`, `6: Бухгалтер`, `7: Админ офиса`

### Konfiguratsiya kalitlari (`tabconfig`)

`port`, `rep_sendmail`, `rep_sendtime`, `rep_lastsend`, `scalesize`,
`rep_issend`, `rep_password`, `comtimeout`, `ShowMass`, `ShowDencity`,
`ShowPressure`, `theme`, `comspeed`

Eslatma: `rep_password` kaliti mavjud, bu jadvalda sezgir ma'lumot bo'lishi mumkin.

## 5) Data Dictionary (to'liq ustunlar)

### `tabchange`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `ChangeID` | `bigint` | NO | `nextval("tabChange_ChangeID_seq")` | PK, smena ID |
| `StartDateTime` | `timestamp` | NO | - | Smena boshlanishi |
| `EndDateTime` | `timestamp` | NO | `now()` | Smena tugashi |
| `OperatorID` | `integer` | NO | - | Operator (inferred FK) |
| `ClosedFlag` | `boolean` | NO | `false` | Smena yopilgan/yo'q |
| `CloseType` | `integer` | NO | `0` | Yopish turi kodi |
| `OpenCounter` | `integer` | YES | `0` | Ochilish counter qiymati |
| `SYNC` | `integer` | NO | `0` | Sync holati (integer flag) |

Constraintlar:
- PK: `tabChange_pkey (ChangeID)`

### `tabconfig`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `id` | `bigint` | NO | `nextval(config_id_seq)` | PK |
| `key` | `varchar` | NO | - | Konfiguratsiya kaliti |
| `val` | `varchar` | YES | - | Konfiguratsiya qiymati |

Constraintlar:
- PK: `config_pkey (id)`

### `tabgastype`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `Num` | `bigint` | NO | `nextval("tabGasType_Num_seq")` | PK |
| `GasName` | `varchar` | NO | - | Gaz nomi |
| `Price` | `integer` | NO | - | Narx |
| `Dencity` | `integer` | NO | - | Zichlik (`Density`) |
| `IsMetan` | `boolean` | NO | `true` | Metan flag |
| `Updated` | `timestamp` | NO | `now()` | So'nggi update |
| `OperatorID` | `integer` | NO | `0` | Operator (optional/inferred) |

Constraintlar:
- PK: `tabGasType_pkey (Num)`

### `tabmaindata`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `DataID` | `bigint` | NO | `nextval("tabMainData_DataID_seq")` | PK |
| `ChangeID` | `integer` | NO | `0` | Smena (inferred FK) |
| `PistoletID` | `integer` | NO | `0` | Pistolet/TRK kanali |
| `OperatorID` | `integer` | NO | `0` | Operator (inferred FK) |
| `Liters` | `integer` | NO | `0` | Hajm (litr) |
| `OrderLiters` | `integer` | NO | `0` | Buyurtma litr |
| `OrderMoney` | `double precision` | NO | `0` | Buyurtma summasi |
| `Price` | `double precision` | NO | `0` | Narx |
| `Discount` | `double precision` | NO | `0` | Chegirma |
| `Mass` | `integer` | NO | `0` | Massa |
| `Dencity` | `integer` | NO | `0` | Zichlik |
| `Pressure` | `integer` | NO | `0` | Bosim |
| `CarNumber` | `varchar` | NO | `0` | Avto raqam |
| `DateTime` | `timestamp` | NO | `now()` | Tranzaksiya vaqti |
| `GasMetan` | `integer` | NO | `0` | Gaz turi kodi |
| `SYNC` | `boolean` | NO | `false` | Sync holati |
| `MoneyCash` | `double precision` | NO | `0` | Naqd to'lov |
| `MoneyPlastik` | `double precision` | NO | `0` | Plastik karta |
| `MoneyBank` | `double precision` | NO | `0` | Bank to'lovi |
| `MoneyTalon` | `double precision` | NO | `0` | Talon to'lovi |
| `EndCode` | `integer` | YES | - | Yakun kodi |

Constraintlar:
- PK: `tabMainData_pkey (DataID)`

### `taboperator`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `OperatorID` | `bigint` | NO | `nextval("tabOperator_OperatorID_seq")` | PK qismi |
| `Name` | `varchar` | NO | - | PK qismi, login/nom |
| `Password` | `varchar` | NO | - | Unique, parol maydoni |
| `Address` | `varchar` | YES | - | Manzil |
| `Phone` | `varchar` | YES | - | Telefon |
| `Date` | `timestamp` | YES | - | Sana |
| `Type` | `integer` | NO | - | Operator roli (inferred FK) |

Constraintlar:
- PK: `tabOperator_pkey (OperatorID, Name)`
- UNIQUE: `MyUniqueFields (Password)`
- UNIQUE: `UniqName (Name)`

### `taboperatortype`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `TypeID` | `bigint` | NO | `nextval("tabOperatorType_TypeID_seq")` | PK |
| `TypeName` | `varchar` | NO | - | Rol nomi |

Constraintlar:
- PK: `tabOperatorType_pkey (TypeID)`

### `tabsummcounter`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `DataID` | `bigint` | NO | `nextval("tabSummCounter_DataID_seq")` | PK |
| `ChangeID` | `integer` | NO | - | Smena ID (inferred FK) |
| `PisNum` | `integer` | NO | - | Pistolet raqami (inferred FK) |
| `EndDateTime` | `timestamp` | NO | - | Yakun vaqti |
| `BeginCounter` | `bigint` | NO | - | Boshlang'ich counter |
| `EndCounter` | `bigint` | NO | - | Yakuniy counter |
| `SYNC` | `boolean` | NO | - | Sync holati |

Constraintlar:
- PK: `tabSummCounter_pkey (DataID)`

### `tabtrk`

| Ustun | Tip | NULL | Default | Izoh |
|---|---|---|---|---|
| `Index` | `bigint` | NO | `nextval("tabTRK_Index_seq")` | PK |
| `TRKID` | `integer` | NO | - | TRK identifikatori |
| `PistoletID` | `integer` | NO | - | Pistolet identifikatori |
| `Half` | `integer` | NO | - | Kanal/yarim liniya belgisi |
| `SumLitr` | `bigint` | NO | `0` | Umumiy litr counter |
| `SmenaLitr` | `integer` | YES | - | Smena litr counter |
| `pistName` | `varchar` | YES | - | Pistolet nomi |
| `trkType` | `integer` | YES | `1` | TRK turi |
| `portName` | `varchar` | YES | - | COM port nomi |

Constraintlar:
- PK: `tabTRK_pkey (Index)`

## 6) Indekslar

Mavjud indekslar asosan PK/UNIQUE indekslardan iborat:

- `tabchange`: `tabChange_pkey`
- `tabconfig`: `config_pkey`
- `tabgastype`: `tabGasType_pkey`
- `tabmaindata`: `tabMainData_pkey`
- `taboperator`: `tabOperator_pkey`, `MyUniqueFields`, `UniqName`
- `taboperatortype`: `tabOperatorType_pkey`
- `tabsummcounter`: `tabSummCounter_pkey`
- `tabtrk`: `tabTRK_pkey`

`tabmaindata` kabi katta jadvalda (`250k+` row) izlash/filtrlash uchun qo'shimcha indekslar
(`DateTime`, `ChangeID`, `OperatorID`, `PistoletID`) yo'qligi performancega ta'sir qilishi mumkin.

## 7) Risklar va takliflar

1. **FK constraintlar yo'q**
   - Hozir data mosligi yaxshi, lekin kelajakda noto'g'ri yozuvlar kirishi mumkin.
   - Tavsiya: inferred bog'lanishlarga FK constraint qo'shish.

2. **Parol saqlanishi**
   - `taboperator.Password` unique text sifatida turibdi.
   - Tavsiya: plain text o'rniga hash (`bcrypt/argon2`) saqlash.

3. **`SYNC` tiplarida nomuvofiqlik**
   - `tabchange.SYNC` = `integer`, `tabmaindata.SYNC` = `boolean`.
   - Tavsiya: yagona data model (bir xil tip)ga keltirish.

4. **Composite PK (`taboperator`)**
   - PK: (`OperatorID`, `Name`) bo'lgani uchun relationlar murakkablashishi mumkin.
   - Tavsiya: faqat `OperatorID` ni PK qoldirish.

5. **Naming va imlo**
   - `Dencity` ehtimol `Density`.
   - Tavsiya: schema naming standard joriy qilish.

## 8) Tezkor tekshiruv so'rovlari

```sql
-- Jadvallar ro'yxati
\dt

-- Har bir jadval row count
SELECT 'tabmaindata', count(*) FROM tabmaindata
UNION ALL SELECT 'tabchange', count(*) FROM tabchange
UNION ALL SELECT 'tabconfig', count(*) FROM tabconfig
UNION ALL SELECT 'tabgastype', count(*) FROM tabgastype
UNION ALL SELECT 'taboperator', count(*) FROM taboperator
UNION ALL SELECT 'taboperatortype', count(*) FROM taboperatortype
UNION ALL SELECT 'tabsummcounter', count(*) FROM tabsummcounter
UNION ALL SELECT 'tabtrk', count(*) FROM tabtrk;
```

