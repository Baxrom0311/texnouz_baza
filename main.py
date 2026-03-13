import argparse
import logging
import os
import signal
import threading
import time

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


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
SYNC_STATE_TABLE = "sync_bridge_state"
DEFAULT_LOCAL_HOST = "127.0.0.1" if os.name == "nt" else "/tmp"

STOP_EVENT = threading.Event()


# Hamma config shu fayl ichida.
LOCAL_DB = {
    "dbname": env_str("LOCAL_DB_NAME", "texnouz_copy"),
    "user": env_str("LOCAL_DB_USER", "baxrom"),
    "password": env_str("LOCAL_DB_PASSWORD"),
    "host": env_str("LOCAL_DB_HOST", DEFAULT_LOCAL_HOST),
    "port": env_int("LOCAL_DB_PORT", 5432),
    "connect_timeout": env_int("LOCAL_DB_CONNECT_TIMEOUT", 5),
    "application_name": env_str("LOCAL_DB_APP_NAME", "texnouz_bridge_local"),
    "keepalives": 1,
    "keepalives_idle": env_int("LOCAL_DB_KEEPALIVES_IDLE", 30),
    "keepalives_interval": env_int("LOCAL_DB_KEEPALIVES_INTERVAL", 10),
    "keepalives_count": env_int("LOCAL_DB_KEEPALIVES_COUNT", 5),
}

REMOTE_DB = {
    "dbname": env_str("REMOTE_DB_NAME", "mms_localhost"),
    "user": env_str("REMOTE_DB_USER", "sync_user1"),
    "password": env_str("REMOTE_DB_PASSWORD", "sync_pass12345"),
    "host": env_str("REMOTE_DB_HOST", "3.122.18.70"),
    "port": env_int("REMOTE_DB_PORT", 5432),
    "connect_timeout": env_int("REMOTE_DB_CONNECT_TIMEOUT", 10),
    "application_name": env_str("REMOTE_DB_APP_NAME", "texnouz_bridge_remote"),
    "keepalives": 1,
    "keepalives_idle": env_int("REMOTE_DB_KEEPALIVES_IDLE", 30),
    "keepalives_interval": env_int("REMOTE_DB_KEEPALIVES_INTERVAL", 10),
    "keepalives_count": env_int("REMOTE_DB_KEEPALIVES_COUNT", 5),
}

TABLE_SYNC_RULES = [
    {
        "name": "tabmaindata_to_operation_operation_texnouz",
        "enabled": True,
        "local_schema": "public",
        "local_table": "tabmaindata",
        "remote_schema": "public",
        "remote_table": "operation_operation_texnouz",
        # Remote jadval tabmaindata bilan bir xil tuzilmada.
        "require_all_local_columns": True,
        "cursor": ("DataID", "DataID"),  # incremental cursor: (local, remote)
        "conflict_columns": ["DataID"],  # remote ON CONFLICT ustun(lar)i
        "sync_from_column": "DateTime",
        "sync_from_value": SYNC_FROM_DATETIME,
        "state_schema": "public",
        "state_table": SYNC_STATE_TABLE,
        "column_map": [
            ("DataID", "DataID"),
            ("ChangeID", "ChangeID"),
            ("PistoletID", "PistoletID"),
            ("OperatorID", "OperatorID"),
            ("Liters", "Liters"),
            ("OrderLiters", "OrderLiters"),
            ("OrderMoney", "OrderMoney"),
            ("Price", "Price"),
            ("Discount", "Discount"),
            ("Mass", "Mass"),
            ("Dencity", "Dencity"),
            ("Pressure", "Pressure"),
            ("CarNumber", "CarNumber"),
            ("DateTime", "DateTime"),
            ("GasMetan", "GasMetan"),
            ("SYNC", "SYNC"),
            ("MoneyCash", "MoneyCash"),
            ("MoneyPlastik", "MoneyPlastik"),
            ("MoneyBank", "MoneyBank"),
            ("MoneyTalon", "MoneyTalon"),
            ("EndCode", "EndCode"),
        ],
    },
]


def clean_config(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if v is not None}


def get_connection(cfg: dict):
    return psycopg2.connect(**clean_config(cfg))


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


def ensure_table_exists(cur, schema: str, table: str, side: str) -> None:
    cur.execute("SELECT to_regclass(%s)", (f"{schema}.{table}",))
    if cur.fetchone()[0] is None:
        raise RuntimeError(f"{side} DBda '{schema}.{table}' jadval topilmadi.")

def fetch_table_columns(cur, schema: str, table: str) -> set:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table),
    )
    return {row[0] for row in cur.fetchall()}

def validate_rule(rule: dict, local_columns: set, remote_columns: set) -> None:
    local_cursor, remote_cursor = rule["cursor"]
    conflict_columns = rule["conflict_columns"]
    column_map = rule["column_map"]

    if not column_map:
        raise RuntimeError(f"{rule['name']}: column_map bo'sh bo'lishi mumkin emas.")

    local_map_columns = [pair[0] for pair in column_map]
    remote_map_columns = [pair[1] for pair in column_map]

    if len(remote_map_columns) != len(set(remote_map_columns)):
        raise RuntimeError(f"{rule['name']}: remote column_map ichida duplicate bor.")

    if local_cursor not in local_map_columns:
        raise RuntimeError(f"{rule['name']}: cursor local ustuni column_map ichida bo'lishi kerak.")
    if remote_cursor not in remote_map_columns:
        raise RuntimeError(f"{rule['name']}: cursor remote ustuni column_map ichida bo'lishi kerak.")

    missing_local = sorted((set(local_map_columns) | {local_cursor}) - local_columns)
    missing_remote = sorted(
        (set(remote_map_columns) | set(conflict_columns) | {remote_cursor}) - remote_columns
    )

    if missing_local:
        raise RuntimeError(f"{rule['name']}: local tableda topilmadi: {missing_local}")
    if missing_remote:
        raise RuntimeError(f"{rule['name']}: remote tableda topilmadi: {missing_remote}")

    sync_from_column = rule.get("sync_from_column")
    if sync_from_column and sync_from_column not in local_columns:
        raise RuntimeError(
            f"{rule['name']}: sync_from_column local tableda topilmadi: {sync_from_column}"
        )

    if rule.get("require_all_local_columns", False):
        unmapped_local = sorted(local_columns - set(local_map_columns))
        if unmapped_local:
            raise RuntimeError(
                f"{rule['name']}: local tabledagi barcha ustunlar map qilinishi shart. "
                f"Map qilinmaganlar: {unmapped_local}"
            )

    not_mapped_conflicts = [c for c in conflict_columns if c not in remote_map_columns]
    if not_mapped_conflicts:
        raise RuntimeError(
            f"{rule['name']}: conflict column_map ichida yo'q: {not_mapped_conflicts}. "
            "ON CONFLICT ishlashi uchun map qilingan bo'lishi kerak."
        )


def build_upsert_sql(schema: str, table: str, remote_columns: list, conflict_columns: list):
    insert_cols = sql.SQL(", ").join(sql.Identifier(c) for c in remote_columns)
    conflict_cols = sql.SQL(", ").join(sql.Identifier(c) for c in conflict_columns)
    update_columns = [c for c in remote_columns if c not in conflict_columns]

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


def get_remote_cursor_value(cur, schema: str, table: str, remote_cursor_column: str):
    query = sql.SQL("SELECT COALESCE(MAX({col}), 0) FROM {table}").format(
        col=sql.Identifier(remote_cursor_column),
        table=sql.Identifier(schema, table),
    )
    cur.execute(query)
    return cur.fetchone()[0]


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
        return None
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


def fetch_local_batch(
    cur,
    schema: str,
    table: str,
    local_columns: list,
    local_cursor_column: str,
    cursor_value,
    batch_size: int,
    sync_from_column: str = None,
    sync_from_value=None,
):
    conditions = [
        sql.SQL("{cursor_col} > %s").format(cursor_col=sql.Identifier(local_cursor_column))
    ]
    params = [cursor_value]
    if sync_from_column and sync_from_value is not None:
        conditions.append(
            sql.SQL("{from_col} >= %s").format(from_col=sql.Identifier(sync_from_column))
        )
        params.append(sync_from_value)
    params.append(batch_size)

    query = sql.SQL(
        """
        SELECT {cols}
        FROM {table}
        WHERE {where_clause}
        ORDER BY {cursor_col} ASC
        LIMIT %s
        """
    ).format(
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in local_columns),
        table=sql.Identifier(schema, table),
        where_clause=sql.SQL(" AND ").join(conditions),
        cursor_col=sql.Identifier(local_cursor_column),
    )
    cur.execute(query, tuple(params))
    return cur.fetchall()


def fetch_local_last_n(
    cur,
    schema: str,
    table: str,
    local_columns: list,
    local_cursor_column: str,
    last_n: int,
):
    query = sql.SQL(
        """
        SELECT {cols}
        FROM {table}
        ORDER BY {cursor_col} DESC
        LIMIT %s
        """
    ).format(
        cols=sql.SQL(", ").join(sql.Identifier(c) for c in local_columns),
        table=sql.Identifier(schema, table),
        cursor_col=sql.Identifier(local_cursor_column),
    )
    cur.execute(query, (last_n,))
    rows = cur.fetchall()
    rows.reverse()
    return rows


def sync_rule_once(local_conn, remote_conn, rule: dict, batch_size: int) -> int:
    with local_conn.cursor() as local_cur, remote_conn.cursor() as remote_cur:
        ensure_table_exists(local_cur, rule["local_schema"], rule["local_table"], "LOCAL")
        ensure_table_exists(remote_cur, rule["remote_schema"], rule["remote_table"], "REMOTE")

        local_table_columns = fetch_table_columns(local_cur, rule["local_schema"], rule["local_table"])
        remote_table_columns = fetch_table_columns(remote_cur, rule["remote_schema"], rule["remote_table"])
        validate_rule(rule, local_table_columns, remote_table_columns)

        local_columns = [pair[0] for pair in rule["column_map"]]
        remote_columns = [pair[1] for pair in rule["column_map"]]
        local_cursor, remote_cursor = rule["cursor"]
        conflict_columns = rule["conflict_columns"]
        sync_from_column = rule.get("sync_from_column")
        sync_from_value = rule.get("sync_from_value")
        state_schema = rule.get("state_schema", "public")
        state_table = rule.get("state_table", SYNC_STATE_TABLE)

        upsert_sql = build_upsert_sql(
            rule["remote_schema"],
            rule["remote_table"],
            remote_columns,
            conflict_columns,
        )
        upsert_sql_str = upsert_sql.as_string(remote_conn)

        use_state_table = True
        try:
            ensure_sync_state_table(remote_cur, state_schema, state_table)
        except Exception as exc:
            remote_conn.rollback()
            use_state_table = False
            logging.warning(
                "[%s] State table ishlamadi (%s). Fallback: remote max cursor.",
                rule["name"],
                exc,
            )

        if use_state_table:
            cursor_value = get_state_cursor(remote_cur, state_schema, state_table, rule["name"])
            if cursor_value is None:
                cursor_value = get_remote_cursor_value(
                    remote_cur, rule["remote_schema"], rule["remote_table"], remote_cursor
                )
                upsert_state_cursor(remote_cur, state_schema, state_table, rule["name"], cursor_value)
                remote_conn.commit()
                logging.info(
                    "[%s] State init qilindi: %s=%s",
                    rule["name"],
                    remote_cursor,
                    cursor_value,
                )
            remote_max_cursor = get_remote_cursor_value(
                remote_cur, rule["remote_schema"], rule["remote_table"], remote_cursor
            )
            if cursor_value > remote_max_cursor:
                logging.warning(
                    "[%s] State cursor(%s) remote max(%s)dan katta. Cursor remote maxga tushirildi.",
                    rule["name"],
                    cursor_value,
                    remote_max_cursor,
                )
                cursor_value = remote_max_cursor
                upsert_state_cursor(remote_cur, state_schema, state_table, rule["name"], cursor_value)
                remote_conn.commit()
        else:
            cursor_value = get_remote_cursor_value(
                remote_cur, rule["remote_schema"], rule["remote_table"], remote_cursor
            )

        if sync_from_column and sync_from_value is not None:
            logging.info(
                "[%s] Sync start: cursor>%s va %s>='%s'",
                rule["name"],
                cursor_value,
                sync_from_column,
                sync_from_value,
            )
        else:
            logging.info("[%s] Sync start: cursor>%s", rule["name"], cursor_value)

        local_cursor_idx = local_columns.index(local_cursor)
        synced = 0

        while True:
            batch = fetch_local_batch(
                local_cur,
                rule["local_schema"],
                rule["local_table"],
                local_columns,
                local_cursor,
                cursor_value,
                batch_size,
                sync_from_column=sync_from_column,
                sync_from_value=sync_from_value,
            )
            if not batch:
                break

            try:
                execute_values(
                    remote_cur,
                    upsert_sql_str,
                    batch,
                    page_size=min(batch_size, 1000),
                )
                next_cursor = batch[-1][local_cursor_idx]
                if use_state_table:
                    upsert_state_cursor(remote_cur, state_schema, state_table, rule["name"], next_cursor)
                remote_conn.commit()
            except Exception:
                remote_conn.rollback()
                raise

            synced += len(batch)
            cursor_value = next_cursor
            logging.info("[%s] Batch synced=%s, cursor=%s", rule["name"], len(batch), cursor_value)

        if use_state_table and synced == 0:
            upsert_state_cursor(remote_cur, state_schema, state_table, rule["name"], cursor_value)
            remote_conn.commit()
            logging.info("[%s] No new rows. State heartbeat yangilandi: cursor=%s", rule["name"], cursor_value)

        logging.info("[%s] Sync done. Total=%s", rule["name"], synced)
        return synced


def sync_rule_last_n(local_conn, remote_conn, rule: dict, last_n: int) -> int:
    with local_conn.cursor() as local_cur, remote_conn.cursor() as remote_cur:
        ensure_table_exists(local_cur, rule["local_schema"], rule["local_table"], "LOCAL")
        ensure_table_exists(remote_cur, rule["remote_schema"], rule["remote_table"], "REMOTE")

        local_table_columns = fetch_table_columns(local_cur, rule["local_schema"], rule["local_table"])
        remote_table_columns = fetch_table_columns(remote_cur, rule["remote_schema"], rule["remote_table"])
        validate_rule(rule, local_table_columns, remote_table_columns)

        local_columns = [pair[0] for pair in rule["column_map"]]
        remote_columns = [pair[1] for pair in rule["column_map"]]
        local_cursor, _remote_cursor = rule["cursor"]
        conflict_columns = rule["conflict_columns"]

        upsert_sql = build_upsert_sql(
            rule["remote_schema"],
            rule["remote_table"],
            remote_columns,
            conflict_columns,
        )
        upsert_sql_str = upsert_sql.as_string(remote_conn)

        batch = fetch_local_last_n(
            local_cur,
            rule["local_schema"],
            rule["local_table"],
            local_columns,
            local_cursor,
            last_n,
        )
        if not batch:
            logging.info("[%s] Local table bo'sh. Sync qilinmadi.", rule["name"])
            return 0

        execute_values(
            remote_cur,
            upsert_sql_str,
            batch,
            page_size=min(len(batch), 1000),
        )
        remote_conn.commit()

        local_cursor_idx = local_columns.index(local_cursor)
        min_cursor = batch[0][local_cursor_idx]
        max_cursor = batch[-1][local_cursor_idx]
        logging.info(
            "[%s] Last-N sync done. Total=%s, cursor_range=[%s..%s]",
            rule["name"],
            len(batch),
            min_cursor,
            max_cursor,
        )
        return len(batch)


def sync_once(batch_size: int) -> int:
    enabled_rules = [r for r in TABLE_SYNC_RULES if r.get("enabled", True)]
    if not enabled_rules:
        logging.info("Enabled rule topilmadi.")
        return 0

    total = 0
    with get_connection(LOCAL_DB) as local_conn, get_connection(REMOTE_DB) as remote_conn:
        for rule in enabled_rules:
            total += sync_rule_once(local_conn, remote_conn, rule, batch_size)
    return total


def sync_last_n(last_n: int) -> int:
    enabled_rules = [r for r in TABLE_SYNC_RULES if r.get("enabled", True)]
    if not enabled_rules:
        logging.info("Enabled rule topilmadi.")
        return 0

    total = 0
    with get_connection(LOCAL_DB) as local_conn, get_connection(REMOTE_DB) as remote_conn:
        for rule in enabled_rules:
            total += sync_rule_last_n(local_conn, remote_conn, rule, last_n)
    return total


def list_tables(db_cfg: dict, side: str, schema: str = "public") -> None:
    with get_connection(db_cfg) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
                """,
                (schema,),
            )
            rows = [r[0] for r in cur.fetchall()]

    print(f"{side} DB ({schema}) tablelar:")
    if not rows:
        print("- topilmadi")
        return
    for t in rows:
        print(f"- {t}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Local DBdan remote DBga mapping asosida sync qiladi."
    )
    parser.add_argument("--once", action="store_true", help="Bitta marta sync qiladi.")
    parser.add_argument(
        "--last-n",
        type=int,
        default=None,
        help="Har bir enabled rule uchun local jadvaldan eng oxirgi N yozuvni sync qiladi.",
    )
    parser.add_argument(
        "--list-local-tables",
        action="store_true",
        help="Local DBdagi tablelarni ko'rsatadi.",
    )
    parser.add_argument(
        "--list-remote-tables",
        action="store_true",
        help="Remote DBdagi tablelarni ko'rsatadi.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch hajmi (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Loop interval sekund (default: {DEFAULT_INTERVAL_SECONDS})",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    register_signal_handlers()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size 0 dan katta bo'lishi kerak.")
    if args.interval <= 0:
        raise SystemExit("--interval 0 dan katta bo'lishi kerak.")
    if args.last_n is not None and args.last_n <= 0:
        raise SystemExit("--last-n 0 dan katta bo'lishi kerak.")

    if args.list_local_tables:
        list_tables(LOCAL_DB, "LOCAL")
        return

    if args.list_remote_tables:
        list_tables(REMOTE_DB, "REMOTE")
        return

    if args.last_n is not None:
        sync_last_n(args.last_n)
        return

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
