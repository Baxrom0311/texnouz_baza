import argparse
import logging
import os
import signal
import threading
import time
import shutil
import tempfile
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import pyodbc


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def env_str(name: str, default: str = None):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value

def env_int(name: str, default: int):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} butun son bo'lishi kerak, hozirgi qiymat: {value}") from exc


DEFAULT_BATCH_SIZE = env_int("SYNC_BATCH_SIZE", 1000)
DEFAULT_INTERVAL_SECONDS = env_int("SYNC_INTERVAL_SECONDS", 10)
DEFAULT_RETRY_BASE_SECONDS = env_int("SYNC_RETRY_BASE_SECONDS", 5)
DEFAULT_RETRY_MAX_SECONDS = env_int("SYNC_RETRY_MAX_SECONDS", 300)
SYNC_FROM_DATETIME = env_str("SYNC_FROM_DATETIME", "2026-03-01 00:00:00")
SYNC_STATE_TABLE = "sync_bridge_state_v1"

STOP_EVENT = threading.Event()

# Local (MS Access) db3.mdb connection path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_MDB_PATH = env_str("LOCAL_MDB_PATH", os.path.join(SCRIPT_DIR, "..", "app", "Base", "db3.mdb"))

REMOTE_DB = {
    "dbname": env_str("REMOTE_DB_NAME", "mms_localhost"),
    "user": env_str("REMOTE_DB_USER", "sync_user1"),
    "password": env_str("REMOTE_DB_PASSWORD", "sync_pass12345"),
    "host": env_str("REMOTE_DB_HOST", "3.122.18.70"),
    "port": env_int("REMOTE_DB_PORT", 5432),
    "connect_timeout": env_int("REMOTE_DB_CONNECT_TIMEOUT", 10),
    "application_name": env_str("REMOTE_DB_APP_NAME", "texnouz_bridge_remote_v1"),
    "keepalives": 1,
    "keepalives_idle": env_int("REMOTE_DB_KEEPALIVES_IDLE", 30),
    "keepalives_interval": env_int("REMOTE_DB_KEEPALIVES_INTERVAL", 10),
    "keepalives_count": env_int("REMOTE_DB_KEEPALIVES_COUNT", 5),
}

# The target columns in Postgres for operation_operation_texnouz
TARGET_COLUMNS = [
    "DataID", "ChangeID", "PistoletID", "OperatorID", "Liters", "OrderLiters",
    "OrderMoney", "Price", "Discount", "Mass", "Dencity", "Pressure",
    "CarNumber", "DateTime", "GasMetan", "SYNC", "MoneyCash", "MoneyPlastik",
    "MoneyBank", "MoneyTalon", "EndCode"
]

def clean_config(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if v is not None}

def get_remote_connection(cfg: dict):
    return psycopg2.connect(**clean_config(cfg))

def get_local_connection(mdb_path: str):
    # DSN-less connection to MS Access
    # Windows environment is assumed here
    conn_str = (
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={mdb_path};"
    )
    return pyodbc.connect(conn_str)

def request_shutdown(signum=None, _frame=None):
    if signum is None:
        logging.info("Shutdown so'rovi qabul qilindi.")
    else:
        logging.info("Signal qabul qilindi (%s). Bridge to'xtatilmoqda.", signum)
    STOP_EVENT.set()

def register_signal_handlers():
    signal.signal(signal.SIGINT, request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)

def fetch_local_columns(cur, table: str):
    # pyodbc cursor.columns requires table name
    cols = cur.columns(table=table).fetchall()
    return [col.column_name for col in cols]

def build_upsert_sql(schema: str, table: str, columns: list, conflict_columns: list):
    insert_cols = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
    conflict_cols = sql.SQL(", ").join(sql.Identifier(c) for c in conflict_columns)
    update_columns = [c for c in columns if c not in conflict_columns]

    if update_columns:
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

    return sql.SQL(
        """
        INSERT INTO {table} ({insert_cols})
        VALUES %s
        ON CONFLICT ({conflict_cols}) DO NOTHING
        """
    ).format(
        table=sql.Identifier(schema, table),
        insert_cols=insert_cols,
        conflict_cols=conflict_cols,
    )

def ensure_sync_state_table(cur, schema: str, table: str):
    query = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {table} (
            rule_name text PRIMARY KEY,
            last_cursor bigint NOT NULL DEFAULT 0,
            updated_at timestamp with time zone NOT NULL DEFAULT now()
        )
        """
    ).format(table=sql.Identifier(schema, table))
    cur.execute(query)

def get_state_cursor(cur, schema: str, table: str, rule_name: str):
    query = sql.SQL("SELECT last_cursor FROM {table} WHERE rule_name = %s").format(
        table=sql.Identifier(schema, table)
    )
    cur.execute(query, (rule_name,))
    row = cur.fetchone()
    if row is None:
        return 0
    return row[0]

def upsert_state_cursor(cur, schema: str, table: str, rule_name: str, last_cursor):
    query = sql.SQL(
        """
        INSERT INTO {table} (rule_name, last_cursor, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (rule_name) DO UPDATE
        SET last_cursor = EXCLUDED.last_cursor,
            updated_at = now()
        """
    ).format(table=sql.Identifier(schema, table))
    cur.execute(query, (rule_name, last_cursor))

def sync_once(batch_size: int) -> int:
    total_synced = 0
    rule_name = "tabmaindata_v1_to_operation_texnouz_v1"
    remote_schema = "public"
    remote_table = "operation_operation_texnouz_v1"
    conflict_cols = ["DataID"]

    # --- FILE LOCK BYPASS: "Hot Copy" the .mdb file ---
    # Since Texnouz.exe heavily locks the file, we copy it silently first.
    temp_dir = tempfile.gettempdir()
    temp_mdb_path = os.path.join(temp_dir, "sync_temp_db3.mdb")

    try:
        shutil.copy2(LOCAL_MDB_PATH, temp_mdb_path)
    except Exception as e:
        logging.error(f"Fayl nusxasini yaratishda OS blokladi (qattiq qulf): {e}")
        # Agar fayl qattiq bloklangan bo'lsa darhol chiqib ketamiz
        return 0

    try:
        local_conn = get_local_connection(temp_mdb_path)
    except Exception as e:
        logging.error(f"Local MS Access ({temp_mdb_path}) temp bazasiga ulanib bo'lmadi: {e}")
        return 0

    try:
        remote_conn = get_remote_connection(REMOTE_DB)
    except Exception as e:
        logging.error(f"Remote PostgreSQL bazasiga ulanib bo'lmadi: {e}")
        local_conn.close()
        return 0

    with local_conn.cursor() as local_cur, remote_conn.cursor() as remote_cur:
        # Get active columns from local access db
        local_active_cols = fetch_local_columns(local_cur, "tabmaindata")
        # Keep only the columns that are present in both local MS Access and target remote table
        # We assume target table has TARGET_COLUMNS
        sync_cols = [c for c in TARGET_COLUMNS if c in local_active_cols]
        if not sync_cols:
            logging.error("O'qish uchun umumiy ustunlar topilmadi.")
            return 0
        if "DataID" not in sync_cols:
            logging.error("DataID ustuni topilmadi (PRIMARY KEY xato).")
            return 0

        # Create upsert SQL for Postgres
        upsert_sql_str = build_upsert_sql(remote_schema, remote_table, sync_cols, conflict_cols).as_string(remote_conn)

        # Handle Postgres checkpoint state
        ensure_sync_state_table(remote_cur, remote_schema, SYNC_STATE_TABLE)
        cursor_value = get_state_cursor(remote_cur, remote_schema, SYNC_STATE_TABLE, rule_name)

        logging.info("[%s] Sync start: cursor > %s", rule_name, cursor_value)

        while True:
            # pyodbc param
            query = f"""
                SELECT TOP {batch_size} {", ".join(sync_cols)} 
                FROM tabmaindata 
                WHERE DataID > ? 
                ORDER BY DataID ASC
            """
            try:
                local_cur.execute(query, cursor_value)
                rows = local_cur.fetchall()
            except Exception as e:
                logging.error(f"Local Access DBdan o'qishda xatolik: {e}")
                break
            
            if not rows:
                break
            
            # Convert pyodbc Row objects to tuples
            batch = [tuple(row) for row in rows]
            
            try:
                execute_values(
                    remote_cur,
                    upsert_sql_str,
                    batch,
                    page_size=min(batch_size, 1000)
                )
                next_cursor = batch[-1][sync_cols.index("DataID")]
                upsert_state_cursor(remote_cur, remote_schema, SYNC_STATE_TABLE, rule_name, next_cursor)
                remote_conn.commit()
            except Exception as e:
                remote_conn.rollback()
                logging.error(f"Remote DBga yozishda xatolik: {e}")
                raise

            total_synced += len(batch)
            cursor_value = next_cursor
            logging.info("[%s] Batch synced=%s, cursor=%s", rule_name, len(batch), cursor_value)

        logging.info("[%s] Sync done. Total=%s", rule_name, total_synced)

    local_conn.close()
    remote_conn.close()
    return total_synced

def main():
    parser = argparse.ArgumentParser(description="TexnoUz v1 (MS Access) to Remote PostgreSQL (v2 kabi)")
    parser.add_argument("--once", action="store_true", help="Bitta marta sync qiladi.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)
    args = parser.parse_args()

    register_signal_handlers()

    if args.once:
        sync_once(args.batch_size)
        return

    retry_delay = DEFAULT_RETRY_BASE_SECONDS
    while not STOP_EVENT.is_set():
        try:
            sync_once(args.batch_size)
            retry_delay = DEFAULT_RETRY_BASE_SECONDS
            STOP_EVENT.wait(args.interval)
        except Exception as exc:
            logging.exception("Sync xatosi: %s", exc)
            logging.info("Qayta urinish %s sekunddan keyin.", retry_delay)
            STOP_EVENT.wait(retry_delay)
            retry_delay = min(retry_delay * 2, DEFAULT_RETRY_MAX_SECONDS)

    logging.info("Bridge jarayoni yakunlandi.")

if __name__ == "__main__":
    main()
