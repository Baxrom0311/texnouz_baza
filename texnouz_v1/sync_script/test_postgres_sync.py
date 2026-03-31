import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import datetime

# Faqat qaysi bazaga ulanish kerakligi (xuddi sync_v1.py dagi kabi)
REMOTE_DB = {
    "dbname": "mms_localhost",
    "user": "sync_user1",
    "password": "sync_pass12345",
    "host": "3.122.18.70", # Lokal test uchun: "127.0.0.1" ga almashtiring, agar psql shu Mac'da yoqilgan bo'lsa
    "port": 5432,
    "connect_timeout": 10
}

TARGET_TABLE = "operation_operation_texnouz_v1"

# Remote Postgres bazaga yoziluvchi columnlar
COLUMNS = [
    "DataID", "ChangeID", "PistoletID", "OperatorID", "Liters", "OrderLiters",
    "OrderMoney", "Price", "Discount", "Mass", "Dencity", "Pressure",
    "CarNumber", "DateTime", "GasMetan", "SYNC", "MoneyCash", "MoneyPlastik",
    "MoneyBank", "MoneyTalon", "EndCode"
]

def build_upsert_sql(schema: str, table: str, columns: list, conflict_columns: list):
    insert_cols = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
    conflict_cols = sql.SQL(", ").join(sql.Identifier(c) for c in conflict_columns)
    update_columns = [c for c in columns if c not in conflict_columns]

    updates = sql.SQL(", ").join(
        sql.SQL("{c}=EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in update_columns
    )
    return sql.SQL(
        """
        INSERT INTO {table} ({insert_cols})
        VALUES %s
        ON CONFLICT ({conflict_cols}) DO UPDATE
        SET {updates}
        """
    ).format(
        table=sql.Identifier(schema, table),
        insert_cols=insert_cols,
        conflict_cols=conflict_cols,
        updates=updates,
    )

def test_insert_fake_data():
    try:
        print("PostgreSQL bazasiga ulanishga urinmoqdamiz...")
        conn = psycopg2.connect(**REMOTE_DB)
        print("Ulanish muvaffaqiyatli!")
    except Exception as e:
        print(f"\nXATOLIK: Baza topilmadi yoki ulanish paroli/IP si noto'g'ri!\n{e}")
        return

    with conn.cursor() as cur:
        # SQL upsert so'zini tayyorlaymiz
        upsert_sql_str = build_upsert_sql("public", TARGET_TABLE, COLUMNS, ["DataID"]).as_string(conn)
        
        # 3 ta FAKE ma'lumot (tranzaksiya) qatori:
        fake_rows = [
            (999001, 10, 1, 101, 20000, 20000, 50000, 2500, 0, 0, 0, 0, "01A123BC", datetime.now(), 0, False, 50000, 0, 0, 0, 0),
            (999002, 10, 2, 101, 40000, 40000, 100000, 2500, 0, 0, 0, 0, "10X999YY", datetime.now(), 0, False, 0, 100000, 0, 0, 0),
            (999003, 10, 3, 102, 10000, 10000, 25000, 2500, 0, 0, 0, 0, "YOOQ",    datetime.now(), 0, False, 25000, 0, 0, 0, 0)
        ]

        print(f"\n{TARGET_TABLE} jadvaliga 3 ta uydirma tranzaksiya(fake) ma'lumoti yuborilmoqda...")
        try:
            execute_values(cur, upsert_sql_str, fake_rows, page_size=10)
            conn.commit()
            print("MUVAFFAQIYAT! Ma'lumotlar bazaga muvaffaqiyatli yozildi.")
            print(f"DataID = 999001, 999002, 999003 tekshirib ko'rishingiz mumkin.")
        except Exception as e:
            conn.rollback()
            print(f"\nYozishda xatolik yuz berdi! Jadval ochilmagan bo'lishi mumkin:\n{e}")
            print(f"Iltimos, avval 'create_operation_operation_texnouz_v1.sql' faylini serverda ishga tushiring.")

    conn.close()

if __name__ == "__main__":
    test_insert_fake_data()
