import logging
import time
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values

try:
    from logger import _print
except ImportError:
    def _print(message, level="info"):
        log_method = getattr(logging, level.lower(), logging.info)
        log_method(message)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


LOCAL_DB = {
    "dbname": "ugaz_arm",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5438,
}

REMOTE_DB = {
    "dbname": "mms_localhost",
    "user": "sync_user1",
    "password": "sync_pass12345",
    "host": "18.156.69.195",
    "port": 5432,
}


SYNC_INTERVAL = 10
BATCH_SIZE = 500
MAX_BATCHES_PER_TABLE = 1

TABLES = {
    "operation_operation": [
        "id",
        "created_at",
        "updated_at",
        "price",
        "amount",
        "volume",
        "total_volume",
        "total_amount",
        "temperature",
        "pressure",
        "rnn",
        "payment_date",
        "payment_fiscal_status",
        "is_paid",
        "status",
        "pts_transaction_id",
        "dispenser_id",
        "shift_id",
        "user_id",
        "video_record_id",
        "external_id",
        "fiscal_id",
    ],
    "video_recording_car": [
        "id",
        "created_at",
        "updated_at",
        "number",
        "model",
        "car_type",
        "car_body",
        "color",
        "owner_type",
        "manufacture_year",
        "fuel_type",
        "tech_status",
        "date",
        "tech_inspection_date",
        "tech_document_number",
        "next_tech_inspection_date",
        "confirmed",
        "external_id",
    ],
    "video_recording_videorecord": [
        "id",
        "created_at",
        "updated_at",
        "is_operated",
        "car_id",
        "dispenser_id",
        "external_id",
        "is_confirmed",
        "current_shift_id",
    ],
    "shift_shift": [
        "id",
        "created_at",
        "updated_at",
        "date_opened",
        "date_closed",
        "is_open",
        "user_id",
        "external_id",
        "closed_user_id",
    ],
}


def get_connection(config):
    return psycopg2.connect(**config)


def get_last_sync(remote_cursor, table_name):
    remote_cursor.execute(
        "SELECT last_sync FROM sync_metadata WHERE table_name = %s",
        (table_name,),
    )
    row = remote_cursor.fetchone()
    return row[0] if row else datetime(2025, 6, 1)


def update_last_sync(remote_cursor, table_name, sync_time):
    remote_cursor.execute(
        """
        INSERT INTO sync_metadata (table_name, last_sync)
        VALUES (%s, %s)
        ON CONFLICT (table_name)
        DO UPDATE SET last_sync = EXCLUDED.last_sync
        """,
        (table_name, sync_time),
    )


def generate_upsert_sql(table, columns):
    col_str = ", ".join(columns)
    set_clause = ", ".join(
        [f"{col} = EXCLUDED.{col}" for col in columns if col != "id"]
    )
    return f"""
        INSERT INTO {table} ({col_str})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET {set_clause}
    """


def sync_table(local_cursor, remote_cursor, table_name, columns):
    try:
        stored_last_sync = get_last_sync(remote_cursor, table_name)
        current_last_sync = stored_last_sync
        current_last_id = 0
        latest_sync_time = stored_last_sync
        reached_end_of_rows = False
        synced_total = 0

        upsert_query = generate_upsert_sql(table_name, columns)
        updated_at_idx = columns.index("updated_at")
        id_idx = columns.index("id")

        for batch_no in range(1, MAX_BATCHES_PER_TABLE + 1):
            local_cursor.execute(
                f"""
                SELECT {', '.join(columns)}
                FROM {table_name}
                WHERE updated_at > %s
                   OR (updated_at = %s AND id > %s)
                ORDER BY updated_at ASC, id ASC
                LIMIT %s
                """,
                (current_last_sync, current_last_sync, current_last_id, BATCH_SIZE),
            )
            rows = local_cursor.fetchall()
            row_count = len(rows)

            if row_count == 0:
                if synced_total == 0:
                    logging.info("No new rows to sync for table '%s'.", table_name)
                reached_end_of_rows = True
                break

            execute_values(
                remote_cursor,
                upsert_query,
                rows,
                page_size=min(row_count, 1000),
            )

            latest_row = rows[-1]
            current_last_sync = latest_row[updated_at_idx]
            current_last_id = latest_row[id_idx]
            latest_sync_time = current_last_sync
            synced_total += row_count

            _print(
                f"Batch {batch_no}: {row_count} row sync qilindi for table '{table_name}'."
            )

            if row_count < BATCH_SIZE:
                reached_end_of_rows = True
                break

        if synced_total == 0:
            return

        if reached_end_of_rows:
            update_last_sync(remote_cursor, table_name, latest_sync_time)
        else:
            safe_sync_time = latest_sync_time - timedelta(microseconds=1)
            update_last_sync(remote_cursor, table_name, safe_sync_time)

        _print(f"Synced {synced_total} rows for table '{table_name}'.")

    except Exception as e:
        _print(f"Error syncing table '{table_name}': {e}", level="error")


def sync_loop():
    while True:
        try:
            logging.info("Starting sync process...")
            with get_connection(LOCAL_DB) as local_conn, get_connection(REMOTE_DB) as remote_conn:
                local_cursor = local_conn.cursor()
                remote_cursor = remote_conn.cursor()

                for table, columns in TABLES.items():
                    sync_table(local_cursor, remote_cursor, table, columns)

                remote_conn.commit()
                _print("All tables synced successfully.")
        except Exception as e:
            logging.error(f"Sync loop error: {e}", exc_info=True)
            _print(f"Sync loop error: {e}", level="error")
        finally:
            logging.info(f"Sleeping for {SYNC_INTERVAL} seconds before next attempt.")
            time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    sync_loop()
