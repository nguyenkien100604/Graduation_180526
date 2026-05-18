# -*- coding: utf-8 -*-
"""Cấu hình kết nối SQL Server (SSMS) — đọc từ biến môi trường / file .env."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = _PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


_load_dotenv()


def get_connection_string() -> str:
    server = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
    database = os.getenv("DB_NAME", "GraduationBanking")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() in ("1", "yes", "true")

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        "TrustServerCertificate=yes",
    ]
    if trusted:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={os.getenv('DB_USER', '')}")
        parts.append(f"PWD={os.getenv('DB_PASSWORD', '')}")
    return ";".join(parts) + ";"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    odbc = quote_plus(get_connection_string())
    return create_engine(f"mssql+pyodbc:///?odbc_connect={odbc}", fast_executemany=True)


def schema_name() -> str:
    return os.getenv("DB_SCHEMA", "dbo")


def transactions_table() -> str:
    return os.getenv("DB_TABLE_TRANSACTIONS", "Transactions")


def backup_table() -> str:
    return os.getenv("DB_TABLE_BACKUP", "Transactions_Backup")


def isolation_table() -> str:
    return os.getenv("DB_TABLE_ISOLATION", "IsolationOutput")


def rfm_table() -> str:
    return os.getenv("DB_TABLE_RFM", "RankRFM")


def anomaly_table() -> str:
    """Alias cũ — dùng isolation_table()."""
    return isolation_table()


def qualified(table: str) -> str:
    return f"{schema_name()}.{table}"


def database_label() -> str:
    return f"{os.getenv('DB_NAME', 'GraduationBanking')}.{qualified(transactions_table())}"


def test_connection() -> tuple[bool, str]:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text("SELECT DB_NAME() AS db, @@SERVERNAME AS srv")).mappings().first()
            if row is None:
                return False, "empty result"
        return True, f"{row['srv']} / {row['db']}"
    except Exception as e:
        return False, str(e)
