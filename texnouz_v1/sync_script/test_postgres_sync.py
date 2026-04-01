import os
import pg8000.dbapi
from datetime import datetime

# Faqat qaysi bazaga ulanish kerakligi (xuddi sync_v1.py dagi kabi)
REMOTE_DB = {
    "database": "mms_localhost",
    "user": "sync_user1",
    "password": "sync_pass12345",
    "host": "3.122.18.70", 
    "port": 5432
}

TARGET_TABLE = "operation_operation_texnouz_v1"

# Remote Postgres bazaga yoziluvchi columnlar
COLUMNS = [
    "DataID", "OperationID", "ChangeID", "CisternID", "PistoletID", "OperatorID", 
    "PartnerID", "GasMetan", "DateTime", "Liters", "OrderLiters", "OrderMoney", 
    "Price", "Discount", "Mass", "Dencity", "Pressure", "WaterLevel", 
    "FuelLevel", "Tempr", "CarNumber", "MoneyCash", "MoneyPlastik", 
    "MoneyBank", "MoneyTalon", "EndCode", "SYNC"
]

# No extra helper needed for pg8000 simple execute

def test_insert_fake_data():
    try:
        print("PostgreSQL bazasiga ulanishga urinmoqdamiz...")
        conn = pg8000.dbapi.connect(**REMOTE_DB)
        print("Ulanish muvaffaqiyatli!")
    except Exception as e:
        print(f"\nXATOLIK: Baza topilmadi yoki ulanish paroli/IP si noto'g'ri!\n{e}")
        return

    with conn.cursor() as cur:
        placeholders = ", ".join(["%s"] * len(COLUMNS))
        cols_str = ", ".join(f'"{c}"' for c in COLUMNS)
        conflict_cols = '"DataID"'
        update_cols = ", ".join(f'"{c}"=EXCLUDED."{c}"' for c in COLUMNS if c != "DataID")
        
        upsert_sql = f"""
            INSERT INTO "public"."{TARGET_TABLE}" ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_cols}) DO UPDATE
            SET {update_cols}
        """
        
        # 3 ta FAKE ma'lumot (tranzaksiya) qatori:
        # DataID, OperationID, ChangeID, CisternID, PistoletID, OperatorID, PartnerID, GasMetan, DateTime, Liters, ...
        now = datetime.now()
        fake_rows = [
            (999001, 11, 10, 1, 1, 101, 0, 0, now, 20.0, 20.0, 50000.0, 2500.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0, "01A123BC", 50000.0, 0.0, 0.0, 0.0, 0, 0),
            (999002, 11, 10, 1, 2, 101, 0, 0, now, 40.0, 40.0, 100000.0, 2500.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0, "10X999YY", 0.0, 100000.0, 0.0, 0.0, 0, 0),
            (999003, 11, 10, 1, 3, 102, 0, 0, now, 10.0, 10.0, 25000.0, 2500.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 20.0, "YOOQ", 25000.0, 0.0, 0.0, 0.0, 0, 0)
        ]

        print(f"\n{TARGET_TABLE} jadvaliga 3 ta uydirma tranzaksiya(fake) ma'lumoti yuborilmoqda...")
        try:
            for row in fake_rows:
                cur.execute(upsert_sql, row)
            conn.commit()
            print("MUVAFFAQIYAT! Ma'lumotlar bazaga muvaffaqiyatli yozildi.")
        except Exception as e:
            conn.rollback()
            print(f"\nYozishda xatolik yuz berdi! Jadval ochilmagan bo'lishi mumkin:\n{e}")

    conn.close()

if __name__ == "__main__":
    test_insert_fake_data()
