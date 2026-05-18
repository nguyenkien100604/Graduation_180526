# -*- coding: utf-8 -*-
"""Helper đọc/ghi SQL cho notebook ETL (input + output)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_TOOLS_DIR = Path(__file__).resolve().parent


def ensure_tools_path() -> Path:
    if str(_TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(_TOOLS_DIR))
    return _TOOLS_DIR


def test_sql_connection() -> tuple[bool, str]:
    ensure_tools_path()
    from db_config import test_connection

    return test_connection()


def load_transactions() -> pd.DataFrame:
    ensure_tools_path()
    from ingest_core import load_all_transactions

    return load_all_transactions()


def load_rank_rfm() -> pd.DataFrame:
    ensure_tools_path()
    from db_config import get_engine, rfm_table

    sql = f"SELECT Segment, Scores FROM dbo.{rfm_table()} ORDER BY Segment"
    return pd.read_sql(sql, get_engine())


def load_isolation_output() -> pd.DataFrame:
    ensure_tools_path()
    from db_config import get_engine, isolation_table

    sql = (
        f"SELECT TransactionID, CustomerID, IsAnomaly, AnomalyLabel "
        f"FROM dbo.{isolation_table()} ORDER BY TransactionID"
    )
    return pd.read_sql(sql, get_engine())


def save_rank_rfm_lookup() -> int:
    ensure_tools_path()
    from ingest_core import save_rank_rfm_lookup as _save

    return _save()


def save_isolation_output(df: pd.DataFrame) -> int:
    ensure_tools_path()
    from ingest_core import save_isolation_output as _save

    return _save(df)


def sql_table_summary() -> pd.DataFrame:
    """Số dòng các bảng chính — dùng hiển thị trong notebook."""
    ensure_tools_path()
    from db_config import get_engine, isolation_table, rfm_table, transactions_table
    from sqlalchemy import text

    tables = {
        "Transactions": transactions_table(),
        "RankRFM": rfm_table(),
        "IsolationOutput": isolation_table(),
    }
    rows = []
    with get_engine().connect() as conn:
        for label, name in tables.items():
            n = conn.execute(text(f"SELECT COUNT(*) FROM dbo.[{name}]")).scalar()
            rows.append({"Table": f"dbo.{name}", "Rows": int(n or 0)})
    return pd.DataFrame(rows)
