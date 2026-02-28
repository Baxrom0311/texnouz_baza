import time
import psycopg2
from datetime import datetime
import logging

from logger import _print

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Configuration ---
LOCAL_DB = {
    'dbname': 'ugaz_arm',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5438,
}

REMOTE_DB = {
    'dbname': 'mms_localhost',
    'user': 'sync_user1',
    'password': 'sync_pass12345',
    'host': '18.156.69.195',
    'port': 5432,
}


SYNC_INTERVAL = 10  # seconds

TABLES = {
    'operation_operation': [
        'id', 'created_at', 'updated_at', 'price', 'amount', 'volume', 'total_volume', 'total_amount',
        'temperature', 'pressure', 'rnn', 'payment_date', 'payment_fiscal_status', 'is_paid', 'status',
        'pts_transaction_id', 'dispenser_id', 'shift_id', 'user_id', 'video_record_id', 'external_id', 'fiscal_id'
    ],
    'video_recording_car': [
        'id', 'created_at', 'updated_at', 'number', 'model', 'car_type', 'car_body', 'color', 'owner_type',
        'manufacture_year', 'fuel_type', 'tech_status', 'date', 'tech_inspection_date', 'tech_document_number',
        'next_tech_inspection_date', 'confirmed', 'external_id'
    ],
    'video_recording_videorecord': [
        'id', 'created_at', 'updated_at', 'is_operated', 'car_id', 'dispenser_id',
        'external_id', 'is_confirmed', 'current_shift_id'
    ],
    'shift_shift': [
        'id', 'created_at', 'updated_at', 'date_opened', 'date_closed', 'is_open', 'user_id', 'external_id', 'closed_user_id'
    ]
}


def get_connection(config):
    return psycopg2.connect(**config)


def get_last_sync(remote_cursor, table_name):
    remote_cursor.execute(
        "SELECT last_sync FROM sync_metadata WHERE table_name = %s", (table_name,)
    )
    row = remote_cursor.fetchone()
    return row[0] if row else datetime(2025, 6, 1)


def update_last_sync(remote_cursor, table_name, sync_time):
    remote_cursor.execute("""
        INSERT INTO sync_metadata (table_name, last_sync)
        VALUES (%s, %s)
        ON CONFLICT (table_name)
        DO UPDATE SET last_sync = EXCLUDED.last_sync
    """, (table_name, sync_time))


def generate_upsert_sql(table, columns):
    col_str = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    set_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])
    return f"""
        INSERT INTO {table} ({col_str})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE SET {set_clause}
    """


def sync_table(local_cursor, remote_cursor, table_name, columns):
    try:
        last_sync = get_last_sync(remote_cursor, table_name)

        local_cursor.execute(
            f"SELECT {', '.join(columns)} FROM {table_name} WHERE updated_at > %s", (last_sync,)
        )
        rows = local_cursor.fetchall()
        row_count = len(rows)

        if row_count == 0:
            logging.info(f"No new rows to sync for table '{table_name}'.")
            return

        _print(f"New rows {row_count} for table '{table_name}'.")
        upsert_query = generate_upsert_sql(table_name, columns)

        for row in rows:
            logging.info(f"Execute '{row[0]}'.")
            remote_cursor.execute(upsert_query, row)

        latest_updated_at = max(row[columns.index('updated_at')] for row in rows)
        update_last_sync(remote_cursor, table_name, latest_updated_at)

        _print(f"Synced {row_count} rows for table '{table_name}'.")

    except Exception as e:
        _print(f"Error syncing table '{table_name}': {e}", level='error')


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
            _print(f"Sync loop error: {e}", level='error')
        finally:
            logging.info(f"Sleeping for {SYNC_INTERVAL} seconds before next attempt.")
            time.sleep(SYNC_INTERVAL)


if __name__ == '__main__':
    sync_loop()
