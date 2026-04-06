-- ============================================================
-- Texnouz v1 - To'liq PostgreSQL Schema
-- Manba: Texnouz.exe VMProtect unpack + strings tahlili
-- Sana: 2026-04-06
-- ============================================================

-- Eski jadvallarni o'chirish (agar bo'lsa)
DROP TABLE IF EXISTS tabMainDataHistory CASCADE;
DROP TABLE IF EXISTS tabMainData CASCADE;
DROP TABLE IF EXISTS tabPartnerInHistory CASCADE;
DROP TABLE IF EXISTS tabPartnerOutHistory CASCADE;
DROP TABLE IF EXISTS tabPartnerAccount CASCADE;
DROP TABLE IF EXISTS tabGasHistory CASCADE;
DROP TABLE IF EXISTS tabGoodsPriceHistory CASCADE;
DROP TABLE IF EXISTS tabGoodsHistory CASCADE;
DROP TABLE IF EXISTS tabPriceHistory CASCADE;
DROP TABLE IF EXISTS tabSummCounters CASCADE;
DROP TABLE IF EXISTS tabCardNumbers CASCADE;
DROP TABLE IF EXISTS tabCardTypes CASCADE;
DROP TABLE IF EXISTS tabCarPassport CASCADE;
DROP TABLE IF EXISTS tabGoods CASCADE;
DROP TABLE IF EXISTS tabLevelMeters CASCADE;
DROP TABLE IF EXISTS tabTRK CASCADE;
DROP TABLE IF EXISTS tabStorage CASCADE;
DROP TABLE IF EXISTS tabChange CASCADE;
DROP TABLE IF EXISTS tabPartner CASCADE;
DROP TABLE IF EXISTS tabOperator CASCADE;
DROP TABLE IF EXISTS tabOperatorType CASCADE;
DROP TABLE IF EXISTS tabGasType CASCADE;
DROP TABLE IF EXISTS tabOperation CASCADE;
DROP TABLE IF EXISTS tabErrors CASCADE;
DROP TABLE IF EXISTS tabTaxes CASCADE;
DROP TABLE IF EXISTS tabTaxsTypes CASCADE;
DROP TABLE IF EXISTS tabSchema CASCADE;
DROP TABLE IF EXISTS tabVersion CASCADE;

-- ============================================================
-- 1. LOOKUP / REFERENCE jadvallar
-- ============================================================

CREATE TABLE tabOperatorType (
    TypeID    SERIAL PRIMARY KEY,
    TypeName  VARCHAR(15)
);

CREATE TABLE tabErrors (
    CodeID    SERIAL PRIMARY KEY,
    ErrorName VARCHAR(50)
);

CREATE TABLE tabCardTypes (
    CTNum  SERIAL PRIMARY KEY,
    CTName VARCHAR(20) UNIQUE
);

CREATE TABLE tabTaxsTypes (
    TTID  SERIAL PRIMARY KEY,
    Name  VARCHAR(20)
);

CREATE TABLE tabOperation (
    OperationID SERIAL PRIMARY KEY,
    Name        VARCHAR(50)
);

-- ============================================================
-- 2. ASOSIY JADVALLAR
-- ============================================================

CREATE TABLE tabOperator (
    OperatorID SERIAL PRIMARY KEY,
    AZSID      INT,
    Name       VARCHAR(50),
    Password   VARCHAR(10) UNIQUE,
    Address    VARCHAR(50),
    Phone      VARCHAR(50),
    Date       TIMESTAMP,
    Type       INT REFERENCES tabOperatorType(TypeID)
);

CREATE TABLE tabPartner (
    PartnerID  SERIAL PRIMARY KEY,
    Name       VARCHAR(50),
    Address    VARCHAR(50),
    Phone      VARCHAR(50),
    Enabled    BOOLEAN DEFAULT TRUE,
    DateTime   TIMESTAMP,
    OperatorID INT REFERENCES tabOperator(OperatorID)
);

CREATE TABLE tabGasType (
    Num        SERIAL PRIMARY KEY,
    GasID      INT UNIQUE,
    GasName    VARCHAR(50),
    CheckName  VARCHAR(50),
    Price      DECIMAL(15,2),
    Discount1  INT DEFAULT 0,
    Discount2  INT DEFAULT 0,
    Discount3  INT DEFAULT 0,
    MTaxTypes  VARCHAR(8),
    Dencity    INT,
    GasMetan   INT DEFAULT 0,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    DateTime   TIMESTAMP
);

CREATE TABLE tabStorage (
    Num        SERIAL PRIMARY KEY,
    CisternID  INT UNIQUE,
    GasID      INT REFERENCES tabGasType(GasID),
    Volume     INT DEFAULT 0,
    Date       TIMESTAMP,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    SYNC       BOOLEAN DEFAULT FALSE
);

CREATE TABLE tabTaxes (
    TaxID      SERIAL PRIMARY KEY,
    Name       VARCHAR(10),
    Percent    INT,
    TaxType    INT,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    DateTime   TIMESTAMP
);

CREATE TABLE tabGoods (
    GoodsID    SERIAL PRIMARY KEY,
    Article    INT UNIQUE,
    Divided    BOOLEAN DEFAULT FALSE,
    Enabled    BOOLEAN DEFAULT TRUE,
    Taxes      VARCHAR(8),
    Name       VARCHAR(43),
    BarCode    VARCHAR(13) UNIQUE,
    Price      DECIMAL(15,2),
    Discount   INT DEFAULT 0,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    DateTime   TIMESTAMP
);

CREATE TABLE tabCarPassport (
    CarID       SERIAL PRIMARY KEY,
    TalonNumber VARCHAR(12),
    CarNumber   VARCHAR(12) UNIQUE,
    CarType     VARCHAR(10),
    BalloonNum  INT,
    FirmName    VARCHAR(50),
    EndDate     TIMESTAMP,
    OperatorID  INT REFERENCES tabOperator(OperatorID),
    SYNC        BOOLEAN DEFAULT FALSE
);

CREATE TABLE tabCardNumbers (
    Num        SERIAL PRIMARY KEY,
    CardNumber VARCHAR(20) UNIQUE,
    CardType   INT REFERENCES tabCardTypes(CTNum),
    GasID      INT REFERENCES tabGasType(GasID),
    PartnerID  INT REFERENCES tabPartner(PartnerID),
    DiscSchema INT,
    Liters     INT DEFAULT 0,
    EndDate    TIMESTAMP,
    Date       TIMESTAMP,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    Enabled    BOOLEAN DEFAULT TRUE,
    Sold       BOOLEAN DEFAULT FALSE
);

CREATE TABLE tabLevelMeters (
    Num        SERIAL PRIMARY KEY,
    CisternID  INT REFERENCES tabStorage(CisternID),
    LevMetType INT,
    SerialNum  VARCHAR(20),
    LMName     VARCHAR(20),
    ZeroOffset INT DEFAULT 0,
    DateTime   TIMESTAMP
);

-- ============================================================
-- 3. TRK (Yoqilg'i tarqatish kolonkasi)
-- ============================================================

CREATE TABLE tabTRK (
    Index_     SERIAL PRIMARY KEY,
    TRKID      INT,
    CisternID  INT REFERENCES tabStorage(CisternID),
    PistoletID INT,
    Half       INT,
    HorPos     INT,
    VerPos     INT,
    MPort      INT,
    MBaud      INT,
    MUseCnt    BOOLEAN DEFAULT FALSE,
    MUseAvaP   BOOLEAN DEFAULT FALSE,
    MImpuls    VARCHAR(50),
    MMaxCnt    VARCHAR(50)
);

-- ============================================================
-- 4. SMENA (SHIFT)
-- ============================================================

CREATE TABLE tabChange (
    ChangeID      SERIAL PRIMARY KEY,
    StartDateTime TIMESTAMP,
    EndDateTime   TIMESTAMP,
    OperatorID    INT REFERENCES tabOperator(OperatorID),
    ClosedFlag    BOOLEAN DEFAULT FALSE,
    CloseType     INT,
    OpenCounter   INT DEFAULT 0,
    SYNC          BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- 5. ASOSIY TRANZAKSIYALAR
-- ============================================================

CREATE TABLE tabMainData (
    DataID      SERIAL PRIMARY KEY,
    ChangeID    INT REFERENCES tabChange(ChangeID),
    GasID       INT,
    CisternID   INT,
    PartnerID   INT REFERENCES tabPartner(PartnerID),
    OperationID INT REFERENCES tabOperation(OperationID),
    PistoletID  INT,
    Liters      INT DEFAULT 0,           -- * 100 (1 litr = 100)
    OrderLiters INT DEFAULT 0,
    MoneyCash   DECIMAL(15,2) DEFAULT 0,
    MoneyTalon  DECIMAL(15,2) DEFAULT 0,
    MoneyBank   DECIMAL(15,2) DEFAULT 0,
    MoneyFut    DECIMAL(15,2) DEFAULT 0,
    OrderMoney  DECIMAL(15,2) DEFAULT 0,
    Price       DECIMAL(15,2) DEFAULT 0,
    Discount1   INT DEFAULT 0,
    Discount2   INT DEFAULT 0,
    Debet       INT DEFAULT 0,
    Credit      INT DEFAULT 0,
    WaterLevel  INT DEFAULT 0,
    EndCode     INT DEFAULT 0,
    OperatorID  INT REFERENCES tabOperator(OperatorID),
    DateTime    TIMESTAMP,
    CasseID     INT,
    Count       INT DEFAULT 0,
    Article     INT,
    CheckID     INT,
    Mass        INT DEFAULT 0,
    Dencity     INT DEFAULT 0,
    Pressure    INT DEFAULT 0,
    Kbrd        BOOLEAN DEFAULT FALSE,
    SYNC        BOOLEAN DEFAULT FALSE,
    CarNumber   VARCHAR(12),
    GasMetan    INT DEFAULT 0,
    MGasLevel   INT DEFAULT 0,
    CardNumber  VARCHAR(20)
);

CREATE TABLE tabMainDataHistory (
    -- tabMainData bilan bir xil struktura, arxiv uchun
    DataID      INT,                     -- Original DataID (PK emas)
    ChangeID    INT,
    GasID       INT,
    CisternID   INT,
    PartnerID   INT,
    OperationID INT,
    PistoletID  INT,
    Liters      INT DEFAULT 0,
    OrderLiters INT DEFAULT 0,
    MoneyCash   DECIMAL(15,2) DEFAULT 0,
    MoneyTalon  DECIMAL(15,2) DEFAULT 0,
    MoneyBank   DECIMAL(15,2) DEFAULT 0,
    MoneyFut    DECIMAL(15,2) DEFAULT 0,
    OrderMoney  DECIMAL(15,2) DEFAULT 0,
    Price       DECIMAL(15,2) DEFAULT 0,
    Discount1   INT DEFAULT 0,
    Discount2   INT DEFAULT 0,
    Debet       INT DEFAULT 0,
    Credit      INT DEFAULT 0,
    WaterLevel  INT DEFAULT 0,
    EndCode     INT DEFAULT 0,
    OperatorID  INT,
    DateTime    TIMESTAMP,
    CasseID     INT,
    Count       INT DEFAULT 0,
    Article     INT,
    CheckID     INT,
    Mass        INT DEFAULT 0,
    Dencity     INT DEFAULT 0,
    Pressure    INT DEFAULT 0,
    Kbrd        BOOLEAN DEFAULT FALSE,
    SYNC        BOOLEAN DEFAULT FALSE,
    CarNumber   VARCHAR(12),
    GasMetan    INT DEFAULT 0,
    MGasLevel   INT DEFAULT 0,
    CardNumber  VARCHAR(20)
);

-- ============================================================
-- 6. TARIX jadvallar
-- ============================================================

CREATE TABLE tabGasHistory (
    Cnt             SERIAL PRIMARY KEY,
    ChangeID        INT REFERENCES tabChange(ChangeID),
    CisternID       INT REFERENCES tabStorage(CisternID),
    StartGasLevel   INT DEFAULT 0,
    StartWaterLevel INT DEFAULT 0,
    StartLiters     INT DEFAULT 0,
    EndGasLevel     INT DEFAULT 0,
    EndWaterLevel   INT DEFAULT 0,
    EndLiters       INT DEFAULT 0,
    AddLiters       INT DEFAULT 0,       -- Kiritilgan litr * 100
    Date            TIMESTAMP,
    OperatorID      INT REFERENCES tabOperator(OperatorID),
    Density         DOUBLE PRECISION,
    Temperature     INT,
    NumAuto         VARCHAR(20),
    ExpeditorName   VARCHAR(50),
    SalerName       VARCHAR(50),
    NumDocum        INT,
    DateDocum       TIMESTAMP,
    GasMetan        INT DEFAULT 0,
    SYNC            BOOLEAN DEFAULT FALSE
);

CREATE TABLE tabPriceHistory (
    Cnt        SERIAL PRIMARY KEY,
    GasID      INT REFERENCES tabGasType(GasID),
    Price      DECIMAL(15,2),
    Discount1  INT DEFAULT 0,
    Discount2  INT DEFAULT 0,
    Discount3  INT DEFAULT 0,
    DateTime   TIMESTAMP,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    MTaxTypes  VARCHAR(8)
);

CREATE TABLE tabGoodsHistory (
    Num        SERIAL PRIMARY KEY,
    GoodsID    INT REFERENCES tabGoods(GoodsID),
    Article    INT,
    Divided    BOOLEAN,
    Amount     INT,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    ChangeID   INT REFERENCES tabChange(ChangeID),
    Comment    VARCHAR(100),
    DateTime   TIMESTAMP
);

CREATE TABLE tabGoodsPriceHistory (
    Num        SERIAL PRIMARY KEY,
    GoodsID    INT REFERENCES tabGoods(GoodsID),
    Article    INT,
    Divided    BOOLEAN,
    Enabled    BOOLEAN,
    Price      DECIMAL(15,2),
    Discount   INT DEFAULT 0,
    OperatorID INT REFERENCES tabOperator(OperatorID),
    ChangeID   INT REFERENCES tabChange(ChangeID),
    Comment    VARCHAR(100),
    DateTime   TIMESTAMP
);

CREATE TABLE tabSummCounters (
    DataID        SERIAL PRIMARY KEY,
    ChangeID      INT REFERENCES tabChange(ChangeID),
    PistNum       INT,
    EndDateTime   TIMESTAMP,
    BeginCounter  BIGINT DEFAULT 0,
    EndCounter    BIGINT DEFAULT 0,
    SYNC          BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- 7. HAMKOR HISOB
-- ============================================================

CREATE TABLE tabPartnerAccount (
    DataID    SERIAL PRIMARY KEY,
    PartnerID INT REFERENCES tabPartner(PartnerID),
    GasID     INT REFERENCES tabGasType(GasID),
    Debet     INT DEFAULT 0,
    Credit    INT DEFAULT 0,
    DateTime  TIMESTAMP
);

CREATE TABLE tabPartnerInHistory (
    Num        SERIAL PRIMARY KEY,
    PartnerID  INT REFERENCES tabPartner(PartnerID),
    CardID     INT,
    GasID      INT,
    DataID     INT,
    ChangeID   INT,
    Debet      INT DEFAULT 0,
    Credit     INT DEFAULT 0,
    OperatorID INT,
    DateTime   TIMESTAMP
);

CREATE TABLE tabPartnerOutHistory (
    Num        SERIAL PRIMARY KEY,
    PartnerID  INT REFERENCES tabPartner(PartnerID),
    CardID     INT,
    GasID      INT,
    DataID     INT,
    ChangeID   INT,
    Debet      INT DEFAULT 0,
    Credit     INT DEFAULT 0,
    OperatorID INT,
    DateTime   TIMESTAMP
);

-- ============================================================
-- 8. SCHEMA / VERSION
-- ============================================================

CREATE TABLE tabSchema (
    SCHID    SERIAL PRIMARY KEY,
    SchName  VARCHAR(200),
    SchData  VARCHAR(200)
);

CREATE TABLE tabVersion (
    Cnt            SERIAL PRIMARY KEY,
    AZSID          INT,
    VersionRelease INT DEFAULT 0,
    VersionMajor   INT DEFAULT 2,
    VersionMinor   INT DEFAULT 0
);

-- ============================================================
-- Indekslar
-- ============================================================
CREATE INDEX idx_maindata_changeid ON tabMainData(ChangeID);
CREATE INDEX idx_maindata_datetime ON tabMainData(DateTime);
CREATE INDEX idx_maindata_partnerid ON tabMainData(PartnerID);
CREATE INDEX idx_maindata_pistoletid ON tabMainData(PistoletID);
CREATE INDEX idx_maindata_sync ON tabMainData(SYNC);
CREATE INDEX idx_change_closedflag ON tabChange(ClosedFlag);
CREATE INDEX idx_summcounters_changeid ON tabSummCounters(ChangeID);
