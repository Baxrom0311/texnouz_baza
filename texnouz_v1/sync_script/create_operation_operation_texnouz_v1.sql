BEGIN;

CREATE TABLE IF NOT EXISTS public.operation_operation_texnouz_v1 (
    "DataID" bigint NOT NULL,
    "OperationID" integer DEFAULT 0 NOT NULL,
    "ChangeID" integer DEFAULT 0 NOT NULL,
    "CisternID" integer DEFAULT 0 NOT NULL,
    "PistoletID" integer DEFAULT 0 NOT NULL,
    "OperatorID" integer DEFAULT 0 NOT NULL,
    "PartnerID" integer DEFAULT 0 NOT NULL,
    "GasMetan" integer DEFAULT 0 NOT NULL,
    "DateTime" timestamp without time zone DEFAULT now() NOT NULL,
    "Liters" double precision DEFAULT 0 NOT NULL,
    "OrderLiters" double precision DEFAULT 0 NOT NULL,
    "OrderMoney" double precision DEFAULT 0 NOT NULL,
    "Price" double precision DEFAULT 0 NOT NULL,
    "Discount1" double precision DEFAULT 0 NOT NULL,
    "Discount2" double precision DEFAULT 0 NOT NULL,
    "Mass" double precision DEFAULT 0 NOT NULL,
    "Dencity" double precision DEFAULT 0 NOT NULL,
    "Pressure" double precision DEFAULT 0 NOT NULL,
    "WaterLevel" double precision DEFAULT 0,
    "FuelLevel" double precision DEFAULT 0,
    "Tempr" double precision DEFAULT 0,
    "CarNumber" character varying DEFAULT '' NOT NULL,
    "CardNumber" character varying DEFAULT '' NOT NULL,
    "MoneyCash" double precision DEFAULT 0 NOT NULL,
    "MoneyBank" double precision DEFAULT 0 NOT NULL,
    "MoneyTalon" double precision DEFAULT 0 NOT NULL,
    "MoneyFut" double precision DEFAULT 0 NOT NULL,
    "EndCode" integer,
    "SYNC" boolean DEFAULT false NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.operation_operation_texnouz_v1'::regclass
          AND conname = 'operation_operation_texnouz_v1_pkey'
    ) THEN
        ALTER TABLE public.operation_operation_texnouz_v1
            ADD CONSTRAINT operation_operation_texnouz_v1_pkey PRIMARY KEY ("DataID");
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_v1_datetime
    ON public.operation_operation_texnouz_v1 ("DateTime");

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_v1_changeid
    ON public.operation_operation_texnouz_v1 ("ChangeID");

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_v1_pistoletid
    ON public.operation_operation_texnouz_v1 ("PistoletID");

COMMIT;
