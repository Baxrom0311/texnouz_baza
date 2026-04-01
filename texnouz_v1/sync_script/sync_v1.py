import argparse
import logging
import os
import signal
import threading
import time
import shutil
import tempfile
import pg8000.dbapi
from access_parser import AccessParser


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
}

# The target columns in Postgres for operation_operation_texnouz_v1
TARGET_COLUMNS = [
    "DataID", "OperationID", "ChangeID", "CisternID", "PistoletID", "OperatorID", 
    "PartnerID", "GasMetan", "DateTime", "Liters", "OrderLiters", "OrderMoney", 
    "Price", "Discount", "Mass", "Dencity", "Pressure", "WaterLevel", 
    "FuelLevel", "Tempr", "CarNumber", "MoneyCash", "MoneyPlastik", 
    "MoneyBank", "MoneyTalon", "EndCode", "SYNC"
]

def get_remote_connection(cfg: dict):
    return pg8000.dbapi.connect(
        database=cfg.get("dbname"),
        user=cfg.get("user"),
        password=cfg.get("password"),
        host=cfg.get("host"),
        port=int(cfg.get("port", 5432))
    )

def read_local_mdb(mdb_path: str, table_name: str):
    """
    access_parser yordamida MDB faylni binary darajada o'qiydi.
    ODBC drayver ham, parol ham KERAK EMAS!
    Returns: (column_names: list[str], rows: list[dict])
    """
    db = AccessParser(mdb_path)
    table = db.parse_table(table_name)
    # table is a dict of {column_name: [values...]}
    if not table:
        return [], []

    columns = list(table.keys())
    num_rows = len(table[columns[0]]) if columns else 0

    rows = []
    for i in range(num_rows):
        row = {}
        for col in columns:
            row[col] = table[col][i]
        rows.append(row)

    return columns, rows


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


def build_upsert_sql(schema: str, table: str, columns: list, conflict_columns: list):
    insert_cols = ", ".join(f'"{c}"' for c in columns)
    conflict_cols = ", ".join(f'"{c}"' for c in conflict_columns)
    val_placeholders = ", ".join(["%s"] * len(columns))

    update_columns = [c for c in columns if c not in conflict_columns]

    if update_columns:
        updates = ", ".join(f'"{c}"=EXCLUDED."{c}"' for c in update_columns)
        return f"""
            INSERT INTO "{schema}"."{table}" ({insert_cols})
            VALUES ({val_placeholders})
            ON CONFLICT ({conflict_cols}) DO UPDATE
            SET {updates}
        """
    return f"""
        INSERT INTO "{schema}"."{table}" ({insert_cols})
        VALUES ({val_placeholders})
        ON CONFLICT ({conflict_cols}) DO NOTHING
    """


def ensure_sync_state_table(cur, schema: str, table: str):
    query = f"""
        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            rule_name text PRIMARY KEY,
            last_cursor bigint NOT NULL DEFAULT 0,
            updated_at timestamp with time zone NOT NULL DEFAULT now()
        )
        """
    cur.execute(query)

def get_state_cursor(cur, schema: str, table: str, rule_name: str):
    query = f'SELECT last_cursor FROM "{schema}"."{table}" WHERE rule_name = %s'
    cur.execute(query, (rule_name,))
    row = cur.fetchone()
    if row is None:
        return 0
    return row[0]

def upsert_state_cursor(cur, schema: str, table: str, rule_name: str, last_cursor):
    query = f"""
        INSERT INTO "{schema}"."{table}" (rule_name, last_cursor, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (rule_name) DO UPDATE
        SET last_cursor = EXCLUDED.last_cursor,
            updated_at = now()
        """
    cur.execute(query, (rule_name, last_cursor))

def sync_once(batch_size: int) -> int:
    total_synced = 0
    rule_name = "tabmaindata_v1_to_operation_texnouz_v1"
    remote_schema = "public"
    remote_table = "operation_operation_texnouz_v1"
    conflict_cols = ["DataID"]

    # --- FILE LOCK BYPASS: "Hot Copy" the .mdb file ---
    temp_dir = tempfile.gettempdir()
    temp_mdb_path = os.path.join(temp_dir, "sync_temp_db3.mdb")

    logging.info("MDB faylni nusxalash: %s -> %s", LOCAL_MDB_PATH, temp_mdb_path)
    try:
        shutil.copy2(LOCAL_MDB_PATH, temp_mdb_path)
    except Exception as e:
        logging.error(f"Fayl nusxasini yaratishda OS blokladi (qattiq qulf): {e}")
        return 0

    # --- access_parser bilan MDB faylni o'qish (ODBC/parol kerak emas!) ---
    logging.info("access_parser bilan MDB faylni o'qish boshlandi...")
    try:
        all_columns, all_rows = read_local_mdb(temp_mdb_path, "tabmaindata")
    except Exception as e:
        logging.error(f"Local MDB faylni o'qishda xatolik: {e}")
        return 0

    if not all_rows:
        logging.info("tabmaindata jadvalida ma'lumot topilmadi.")
        return 0

    # Case-insensitive column matching
    col_map = {}
    for target_col in TARGET_COLUMNS:
        for actual_col in all_columns:
            if actual_col.lower() == target_col.lower():
                col_map[target_col] = actual_col
                break

    sync_cols = [tc for tc in TARGET_COLUMNS if tc in col_map]
    if not sync_cols:
        logging.error("O'qish uchun umumiy ustunlar topilmadi. MDB ustunlari: %s", all_columns)
        return 0
    if "DataID" not in sync_cols:
        logging.error("DataID ustuni topilmadi (PRIMARY KEY xato). MDB ustunlari: %s", all_columns)
        return 0

    logging.info("Sync uchun ustunlar: %s", sync_cols)
    logging.info("Jami qatorlar MDB dan: %d", len(all_rows))

    # --- Remote PostgreSQL ga ulanish ---
    try:
        remote_conn = get_remote_connection(REMOTE_DB)
    except Exception as e:
        logging.error(f"Remote PostgreSQL bazasiga ulanib bo'lmadi: {e}")
        return 0

    upsert_sql_str = build_upsert_sql(remote_schema, remote_table, sync_cols, conflict_cols)

    with remote_conn.cursor() as remote_cur:
        ensure_sync_state_table(remote_cur, remote_schema, SYNC_STATE_TABLE)
        cursor_value = get_state_cursor(remote_cur, remote_schema, SYNC_STATE_TABLE, rule_name)
        remote_conn.commit()

        logging.info("[%s] Sync start: cursor > %s", rule_name, cursor_value)

        # DataID bo'yicha tartiblash va filter
        data_id_col = col_map["DataID"]
        filtered_rows = [r for r in all_rows if r.get(data_id_col) is not None and r[data_id_col] > cursor_value]
        filtered_rows.sort(key=lambda r: r[data_id_col])

        logging.info("Yangi qatorlar (cursor > %s): %d", cursor_value, len(filtered_rows))

        # Batch bo'yicha yuborish
        for i in range(0, len(filtered_rows), batch_size):
            batch_rows = filtered_rows[i:i + batch_size]
            batch = []
            for row in batch_rows:
                values = tuple(row.get(col_map[c]) for c in sync_cols)
                batch.append(values)

            try:
                remote_cur.executemany(upsert_sql_str, batch)
                next_cursor = batch_rows[-1][data_id_col]
                upsert_state_cursor(remote_cur, remote_schema, SYNC_STATE_TABLE, rule_name, next_cursor)
                remote_conn.commit()
            except Exception as e:
                remote_conn.rollback()
                logging.error(f"Remote DBga yozishda xatolik: {e}")
                raise

            total_synced += len(batch)
            cursor_value = next_cursor
            logging.info("[%s] Batch synced=%s, cursor=%s", rule_name, len(batch), cursor_value)

    remote_conn.close()

    # Temp faylni tozalash
    try:
        os.remove(temp_mdb_path)
    except OSError:
        pass

    logging.info("[%s] Sync done. Total=%s", rule_name, total_synced)
    return total_synced

def main():
    parser = argparse.ArgumentParser(description="TexnoUz v1 (MS Access) to Remote PostgreSQL")
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
