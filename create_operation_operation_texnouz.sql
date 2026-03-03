BEGIN;

CREATE TABLE IF NOT EXISTS public.operation_operation_texnouz (
    "DataID" bigint NOT NULL,
    "ChangeID" integer DEFAULT 0 NOT NULL,
    "PistoletID" integer DEFAULT 0 NOT NULL,
    "OperatorID" integer DEFAULT 0 NOT NULL,
    "Liters" integer DEFAULT 0 NOT NULL,
    "OrderLiters" integer DEFAULT 0 NOT NULL,
    "OrderMoney" double precision DEFAULT 0 NOT NULL,
    "Price" double precision DEFAULT 0 NOT NULL,
    "Discount" double precision DEFAULT 0 NOT NULL,
    "Mass" integer DEFAULT 0 NOT NULL,
    "Dencity" integer DEFAULT 0 NOT NULL,
    "Pressure" integer DEFAULT 0 NOT NULL,
    "CarNumber" character varying DEFAULT 0 NOT NULL,
    "DateTime" timestamp without time zone DEFAULT now() NOT NULL,
    "GasMetan" integer DEFAULT 0 NOT NULL,
    "SYNC" boolean DEFAULT false NOT NULL,
    "MoneyCash" double precision DEFAULT 0 NOT NULL,
    "MoneyPlastik" double precision DEFAULT 0 NOT NULL,
    "MoneyBank" double precision DEFAULT 0 NOT NULL,
    "MoneyTalon" double precision DEFAULT 0 NOT NULL,
    "EndCode" integer
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.operation_operation_texnouz'::regclass
          AND conname = 'operation_operation_texnouz_pkey'
    ) THEN
        ALTER TABLE public.operation_operation_texnouz
            ADD CONSTRAINT operation_operation_texnouz_pkey PRIMARY KEY ("DataID");
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_datetime
    ON public.operation_operation_texnouz ("DateTime");

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_changeid
    ON public.operation_operation_texnouz ("ChangeID");

CREATE INDEX IF NOT EXISTS idx_operation_operation_texnouz_pistoletid
    ON public.operation_operation_texnouz ("PistoletID");

COMMIT;
