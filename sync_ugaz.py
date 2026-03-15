import time
import psycopg2
from psycopg2.extras import execute_values, execute_batch
from datetime import datetime
from datetime import timezone
import logging
import json
from urllib import request

# --- Logging API ---
API_LOG_URL = 'https://core.amusoft.uz/api/logs'
API_SECRET_KEY = 'CHANGE_ME_SECRET'
API_PROJECT = 'ugaz'


def send_api_log(payload):
    body = json.dumps(payload, default=str).encode('utf-8')
    req = request.Request(
        API_LOG_URL,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'X-Secret-Key': API_SECRET_KEY,
        },
        method='POST',
    )
    try:
        request.urlopen(req, timeout=2).read()
    except Exception:
        # Fire-and-forget: intentionally ignore any delivery errors.
        pass


class ApiLogHandler(logging.Handler):
    def emit(self, record):
        payload = {
            'project': API_PROJECT,
            'ts': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'event': getattr(record, 'event', 'log'),
            'message': record.getMessage(),
        }
        for key in ('table', 'rows', 'last_sync', 'last_id', 'error'):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        send_api_log(payload)


def configure_logging():
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(ApiLogHandler())


def log_event(level, event, message, **fields):
    payload = {'event': event}
    payload.update(fields)
    logging.log(level, message, extra=payload)

# --- Configuration ---
LOCAL_DB = {
    'dbname': 'ugaz_arm',
    'user': 'postgres',
    'password': 'postgres',
    'host': '192.168.1.200',
    'port': 5438,
    'connect_timeout': 10,
    'application_name': 'mms_sync_worker',
}

REMOTE_DB = {
    'dbname': 'mms_localhost',
    'user': 'sync_user1',
    'password': 'sync_pass12345',
    'host': '3.122.18.70',
    'port': 5432,
    'connect_timeout': 10,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 3,
    'application_name': 'mms_sync_worker',
}


SYNC_INTERVAL = 10  # seconds
BATCH_SIZE = 500
DEFAULT_LAST_SYNC = datetime(2025, 6, 1)

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


def metadata_has_last_id(remote_cursor):
    remote_cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'sync_metadata'
              AND column_name = 'last_id'
        )
    """)
    return remote_cursor.fetchone()[0]


def get_sync_checkpoint(remote_cursor, table_name, has_last_id):
    if has_last_id:
        remote_cursor.execute(
            "SELECT last_sync, COALESCE(last_id, 0) FROM sync_metadata WHERE table_name = %s",
            (table_name,),
        )
    else:
        remote_cursor.execute(
            "SELECT last_sync FROM sync_metadata WHERE table_name = %s",
            (table_name,),
        )
    row = remote_cursor.fetchone()
    if not row:
        return DEFAULT_LAST_SYNC, 0
    if has_last_id:
        return row[0], row[1]
    return row[0], 0


def update_sync_checkpoint(remote_cursor, table_name, sync_time, last_id, has_last_id):
    if has_last_id:
        remote_cursor.execute(
            """
            INSERT INTO sync_metadata (table_name, last_sync, last_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (table_name)
            DO UPDATE SET
                last_sync = EXCLUDED.last_sync,
                last_id = EXCLUDED.last_id
            """,
            (table_name, sync_time, last_id),
        )
    else:
        remote_cursor.execute(
            """
            INSERT INTO sync_metadata (table_name, last_sync)
            VALUES (%s, %s)
            ON CONFLICT (table_name)
            DO UPDATE SET last_sync = EXCLUDED.last_sync
            """,
            (table_name, sync_time),
        )


def get_next_remote_id(remote_cursor, table_name):
    """Remote DB dan so'ngi MAX(id) ni olib, +1 qaytaradi."""
    remote_cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
    return remote_cursor.fetchone()[0] + 1


def sync_table(local_cursor, remote_cursor, table_name, columns, has_last_id):
    last_sync, last_id = get_sync_checkpoint(remote_cursor, table_name, has_last_id)
    id_idx = columns.index('id')
    external_id_idx = columns.index('external_id')
    updated_at_idx = columns.index('updated_at')

    # UPDATE uchun ustunlar (id va external_id dan tashqari)
    update_columns = [col for col in columns if col not in ('id', 'external_id')]
    update_col_indices = [i for i, col in enumerate(columns) if col not in ('id', 'external_id')]

    total_synced = 0

    while True:
        local_cursor.execute(
            f"""
            SELECT {', '.join(columns)}
            FROM {table_name}
            WHERE (updated_at > %s OR (updated_at = %s AND id > %s))
            ORDER BY updated_at ASC, id ASC
            LIMIT %s
            """,
            (last_sync, last_sync, last_id, BATCH_SIZE),
        )
        rows = local_cursor.fetchall()
        if not rows:
            break

        # Lokal cursor pozitsiyasini saqlaymiz
        local_last_sync = rows[-1][updated_at_idx]
        local_last_id = rows[-1][id_idx]

        # Remote DB da qaysi lokal id lar allaqachon bor ekanini tekshiramiz
        local_ids_str = [str(row[id_idx]) for row in rows]
        remote_cursor.execute(
            f"SELECT external_id FROM {table_name} WHERE external_id = ANY(%s)",
            (local_ids_str,),
        )
        existing_ext_ids = set(r[0] for r in remote_cursor.fetchall())

        # Yangi va mavjud yozuvlarni ajratamiz
        to_insert = []
        to_update = []
        for row in rows:
            if str(row[id_idx]) in existing_ext_ids:
                to_update.append(row)
            else:
                to_insert.append(row)

        # --- YANGI yozuvlarni INSERT qilish (MAX(id) + 1 dan boshlab) ---
        if to_insert:
            next_remote_id = get_next_remote_id(remote_cursor, table_name)

            insert_rows = []
            for row in to_insert:
                row_list = list(row)
                row_list[external_id_idx] = str(row_list[id_idx])  # lokal id → external_id
                row_list[id_idx] = next_remote_id                  # yangi remote id
                next_remote_id += 1
                insert_rows.append(tuple(row_list))

            col_str = ', '.join(columns)
            insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES %s"
            execute_values(remote_cursor, insert_sql, insert_rows, page_size=BATCH_SIZE)

            log_event(
                logging.INFO,
                'rows_inserted',
                f"Inserted {len(to_insert)} new rows into '{table_name}'.",
                table=table_name,
                rows=len(to_insert),
            )

        # --- MAVJUD yozuvlarni UPDATE qilish ---
        if to_update:
            set_clause = ', '.join([f"{col} = %s" for col in update_columns])
            update_sql = f"UPDATE {table_name} SET {set_clause} WHERE external_id = %s"

            update_params = []
            for row in to_update:
                vals = [row[i] for i in update_col_indices]
                vals.append(str(row[id_idx]))  # WHERE external_id = %s
                update_params.append(vals)

            execute_batch(remote_cursor, update_sql, update_params, page_size=BATCH_SIZE)

            log_event(
                logging.INFO,
                'rows_updated',
                f"Updated {len(to_update)} existing rows in '{table_name}'.",
                table=table_name,
                rows=len(to_update),
            )

        # Checkpoint lokal pozitsiyani saqlaydi
        last_sync = local_last_sync
        last_id = local_last_id
        update_sync_checkpoint(remote_cursor, table_name, last_sync, last_id, has_last_id)
        total_synced += len(rows)

    if total_synced == 0:
        log_event(
            logging.INFO,
            'table_no_changes',
            f"No new rows to sync for table '{table_name}'.",
            table=table_name,
        )
    else:
        log_event(
            logging.INFO,
            'table_synced',
            f"Synced {total_synced} rows for table '{table_name}'.",
            table=table_name,
            rows=total_synced,
            last_sync=last_sync,
            last_id=last_id,
        )
    return total_synced


def sync_loop():
    while True:
        try:
            log_event(logging.INFO, 'sync_cycle_started', "Starting sync process...")
            with get_connection(LOCAL_DB) as local_conn, get_connection(REMOTE_DB) as remote_conn:
                local_cursor = local_conn.cursor()
                remote_cursor = remote_conn.cursor()
                has_last_id = metadata_has_last_id(remote_cursor)
                total_synced = 0

                if not has_last_id:
                    log_event(
                        logging.WARNING,
                        'last_id_missing',
                        "sync_metadata.last_id is missing. Add it to avoid missing rows when updated_at ties occur.",
                    )

                for table, columns in TABLES.items():
                    try:
                        total_synced += sync_table(local_cursor, remote_cursor, table, columns, has_last_id)
                        remote_conn.commit()
                    except Exception as table_error:
                        remote_conn.rollback()
                        log_event(
                            logging.ERROR,
                            'table_sync_failed',
                            f"Sync failed for table '{table}': {table_error}",
                            table=table,
                            error=str(table_error),
                        )

                log_event(
                    logging.INFO,
                    'sync_cycle_finished',
                    f"Sync cycle finished. Total rows synced: {total_synced}.",
                    rows=total_synced,
                )
        except Exception as e:
            log_event(
                logging.ERROR,
                'sync_loop_error',
                f"Sync loop error: {e}",
                error=str(e),
            )
        finally:
            log_event(
                logging.INFO,
                'sync_sleep',
                f"Sleeping for {SYNC_INTERVAL} seconds before next attempt.",
            )
            time.sleep(SYNC_INTERVAL)


if __name__ == '__main__':
    configure_logging()
    sync_loop()
