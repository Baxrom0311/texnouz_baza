import argparse
import logging
import os
import time
from datetime import datetime

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def _print(message: str, level: str = "info") -> None:
    log_method = getattr(logging, level.lower(), logging.info)
    log_method(message)


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


def parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "Sana vaqti `YYYY-MM-DD HH:MM:SS` formatida bo'lishi kerak."
        ) from exc


DEFAULT_SYNC_INTERVAL = env_int("TEST_SYNC_INTERVAL", 10)
DEFAULT_BATCH_SIZE = env_int("TEST_SYNC_BATCH_SIZE", 500)
DEFAULT_MAX_BATCHES_PER_TABLE = env_int("TEST_MAX_BATCHES_PER_TABLE", 1)
DEFAULT_INITIAL_SYNC_FROM = parse_dt(
    env_str("TEST_INITIAL_SYNC_FROM", "2025-06-01 00:00:00")
)
SYNC_METADATA_TABLE = "sync_metadata"


LOCAL_DB = {
    "dbname": env_str("LOCAL_DB_NAME", "ugaz_arm"),
    "user": env_str("LOCAL_DB_USER", "postgres"),
    "password": env_str("LOCAL_DB_PASSWORD", "postgres"),
    "host": env_str("LOCAL_DB_HOST", "localhost"),
    "port": env_int("LOCAL_DB_PORT", 5438),
    "connect_timeout": env_int("LOCAL_DB_CONNECT_TIMEOUT", 5),
}

REMOTE_DB = {
    "dbname": env_str("REMOTE_DB_NAME", "mms_localhost"),
    "user": env_str("REMOTE_DB_USER", "sync_user1"),
    "password": env_str("REMOTE_DB_PASSWORD", "sync_pass12345"),
    "host": env_str("REMOTE_DB_HOST", "18.156.69.195"),
    "port": env_int("REMOTE_DB_PORT", 5432),
    "connect_timeout": env_int("REMOTE_DB_CONNECT_TIMEOUT", 10),
}


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


def clean_config(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if v is not None}


def get_connection(config):
    return psycopg2.connect(**clean_config(config))


def ensure_sync_metadata_table(remote_cursor) -> None:
    remote_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_metadata (
            table_name text PRIMARY KEY,
            last_sync timestamp without time zone NOT NULL,
            last_sync_id bigint NOT NULL DEFAULT 0,
            updated_at timestamp with time zone NOT NULL DEFAULT now()
        )
        """
    )
    remote_cursor.execute(
        """
        ALTER TABLE sync_metadata
        ADD COLUMN IF NOT EXISTS last_sync_id bigint NOT NULL DEFAULT 0
        """
    )
    remote_cursor.execute(
        """
        ALTER TABLE sync_metadata
        ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone NOT NULL DEFAULT now()
        """
    )


def get_last_sync(remote_cursor, table_name: str, initial_sync_from: datetime):
    remote_cursor.execute(
        f"SELECT last_sync, last_sync_id FROM {SYNC_METADATA_TABLE} WHERE table_name = %s",
        (table_name,),
    )
    row = remote_cursor.fetchone()
    if row:
        return row[0], row[1]
    return initial_sync_from, 0


def update_last_sync(
    remote_cursor,
    table_name: str,
    sync_time: datetime,
    sync_row_id: int,
) -> None:
    remote_cursor.execute(
        f"""
        INSERT INTO {SYNC_METADATA_TABLE} (table_name, last_sync, last_sync_id, updated_at)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (table_name)
        DO UPDATE SET
            last_sync = EXCLUDED.last_sync,
            last_sync_id = EXCLUDED.last_sync_id,
            updated_at = now()
        """,
        (table_name, sync_time, sync_row_id),
    )


def generate_upsert_sql(connection, table_name: str, columns: list[str]) -> str:
    insert_cols = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
    update_cols = [column for column in columns if column != "id"]
    set_clause = sql.SQL(", ").join(
        sql.SQL("{column} = EXCLUDED.{column}").format(column=sql.Identifier(column))
        for column in update_cols
    )
    query = sql.SQL(
        """
        INSERT INTO {table} ({columns})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET {set_clause}
        """
    ).format(
        table=sql.Identifier(table_name),
        columns=insert_cols,
        set_clause=set_clause,
    )
    return query.as_string(connection)


def fetch_batch(
    local_cursor,
    table_name: str,
    columns: list[str],
    last_sync: datetime,
    last_sync_id: int,
    batch_size: int,
):
    query = sql.SQL(
        """
        SELECT {columns}
        FROM {table}
        WHERE updated_at IS NOT NULL
          AND (
            updated_at > %s
            OR (updated_at = %s AND id > %s)
          )
        ORDER BY updated_at ASC, id ASC
        LIMIT %s
        """
    ).format(
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        table=sql.Identifier(table_name),
    )
    local_cursor.execute(query, (last_sync, last_sync, last_sync_id, batch_size))
    return local_cursor.fetchall()


def sync_table(
    local_cursor,
    remote_cursor,
    remote_conn,
    table_name: str,
    columns: list[str],
    batch_size: int,
    max_batches_per_table: int,
    initial_sync_from: datetime,
) -> int:
    last_sync, last_sync_id = get_last_sync(remote_cursor, table_name, initial_sync_from)
    updated_at_idx = columns.index("updated_at")
    id_idx = columns.index("id")
    upsert_query = generate_upsert_sql(remote_conn, table_name, columns)

    synced_total = 0

    # Bir siklda qancha row ishlashni cheklaymiz, backlog bo'lsa keyingi aylanishga qoldiradi.
    for batch_no in range(1, max_batches_per_table + 1):
        rows = fetch_batch(
            local_cursor,
            table_name,
            columns,
            last_sync,
            last_sync_id,
            batch_size,
        )
        if not rows:
            if synced_total == 0:
                logging.info("No new rows to sync for table '%s'.", table_name)
            break

        execute_values(
            remote_cursor,
            upsert_query,
            rows,
            page_size=min(len(rows), 1000),
        )

        last_row = rows[-1]
        last_sync = last_row[updated_at_idx]
        last_sync_id = last_row[id_idx]
        update_last_sync(remote_cursor, table_name, last_sync, last_sync_id)
        remote_conn.commit()

        synced_total += len(rows)
        _print(
            (
                f"Table '{table_name}' batch {batch_no}: "
                f"{len(rows)} row sync qilindi, cursor=({last_sync}, {last_sync_id})."
            )
        )

        if len(rows) < batch_size:
            break

    if synced_total:
        _print(f"Table '{table_name}' bo'yicha jami {synced_total} row sync qilindi.")

    return synced_total


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch asosida local DBdan remote DBga test sync qiladi."
    )
    parser.add_argument("--once", action="store_true", help="Bitta sync siklini bajaradi.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Har batch uchun row limiti (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--max-batches-per-table",
        type=int,
        default=DEFAULT_MAX_BATCHES_PER_TABLE,
        help=(
            "Har loopda bir jadval uchun nechta batch ishlashini cheklaydi "
            f"(default: {DEFAULT_MAX_BATCHES_PER_TABLE})."
        ),
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_SYNC_INTERVAL,
        help=f"Loop oralig'i sekundlarda (default: {DEFAULT_SYNC_INTERVAL}).",
    )
    parser.add_argument(
        "--initial-sync-from",
        type=parse_dt,
        default=DEFAULT_INITIAL_SYNC_FROM,
        help=(
            "sync_metadata'da cursor bo'lmasa qaysi vaqtdan boshlash "
            f"(default: {DEFAULT_INITIAL_SYNC_FROM:%Y-%m-%d %H:%M:%S})."
        ),
    )
    return parser.parse_args()


def run_sync_cycle(
    batch_size: int,
    max_batches_per_table: int,
    initial_sync_from: datetime,
) -> int:
    total_synced = 0
    with get_connection(LOCAL_DB) as local_conn, get_connection(REMOTE_DB) as remote_conn:
        with local_conn.cursor() as local_cursor, remote_conn.cursor() as remote_cursor:
            ensure_sync_metadata_table(remote_cursor)
            for table_name, columns in TABLES.items():
                total_synced += sync_table(
                    local_cursor,
                    remote_cursor,
                    remote_conn,
                    table_name,
                    columns,
                    batch_size,
                    max_batches_per_table,
                    initial_sync_from,
                )

    return total_synced


def main():
    args = parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size 0 dan katta bo'lishi kerak.")
    if args.max_batches_per_table <= 0:
        raise SystemExit("--max-batches-per-table 0 dan katta bo'lishi kerak.")
    if args.interval <= 0:
        raise SystemExit("--interval 0 dan katta bo'lishi kerak.")

    while True:
        try:
            logging.info("Starting sync process...")
            total_synced = run_sync_cycle(
                args.batch_size,
                args.max_batches_per_table,
                args.initial_sync_from,
            )
            _print(f"Sync cycle tugadi. Jami sync qilingan row: {total_synced}.")
        except Exception as exc:
            logging.error("Sync loop error: %s", exc, exc_info=True)
            _print(f"Sync loop error: {exc}", level="error")

        if args.once:
            break

        logging.info("Sleeping for %s seconds before next attempt.", args.interval)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
