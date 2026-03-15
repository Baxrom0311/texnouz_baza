-- ============================================================
-- Remote DB migration: external_id ga UNIQUE constraint qo'shish
-- Bu migration sync_ugaz.py ishga tushirilishidan OLDIN bajarilishi kerak!
-- ============================================================

BEGIN;

-- 1. Mavjud rowlar uchun: agar external_id NULL bo'lsa, id ni yozib qo'yamiz
UPDATE operation_operation SET external_id = id::text WHERE external_id IS NULL;
UPDATE video_recording_car SET external_id = id::text WHERE external_id IS NULL;
UPDATE video_recording_videorecord SET external_id = id::text WHERE external_id IS NULL;
UPDATE shift_shift SET external_id = id::text WHERE external_id IS NULL;

-- 2. UNIQUE constraint qo'shish (ON CONFLICT ishlashi uchun shart)
ALTER TABLE operation_operation
    ADD CONSTRAINT uq_operation_external_id UNIQUE (external_id);

ALTER TABLE video_recording_car
    ADD CONSTRAINT uq_car_external_id UNIQUE (external_id);

ALTER TABLE video_recording_videorecord
    ADD CONSTRAINT uq_videorecord_external_id UNIQUE (external_id);

ALTER TABLE shift_shift
    ADD CONSTRAINT uq_shift_external_id UNIQUE (external_id);

COMMIT;
