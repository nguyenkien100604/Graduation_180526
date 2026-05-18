# -*- coding: utf-8 -*-
"""Append banking transactions vào SQL Server (SSMS)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db_config import (
    backup_table,
    database_label,
    get_engine,
    qualified,
    schema_name,
    test_connection,
    transactions_table,
)

COLUMNS: list[str] = [
    "TransactionID",
    "CustomerID",
    "TransactionDate",
    "TransactionType",
    "Amount",
    "ProductCategory",
    "ProductSubcategory",
    "BranchCity",
    "BranchLat",
    "BranchLong",
    "Channel",
    "Currency",
    "CreditCardFees",
    "InsuranceFees",
    "LatePaymentAmount",
    "CustomerScore",
    "MonthlyIncome",
    "CustomerSegment",
    "RecommendedOffer",
]

_CATEGORICAL_COLS = [
    c
    for c in COLUMNS
    if c
    not in (
        "TransactionID",
        "CustomerID",
        "TransactionDate",
        "Amount",
        "BranchLat",
        "BranchLong",
        "CreditCardFees",
        "InsuranceFees",
        "LatePaymentAmount",
        "CustomerScore",
        "MonthlyIncome",
    )
]


def master_table_label() -> str:
    return database_label()


def parse_transaction_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _transactions_q() -> str:
    return qualified(transactions_table())


def _backup_q() -> str:
    return qualified(backup_table())


def table_row_count() -> int:
    engine = get_engine()
    sql = f"SELECT COUNT(*) AS n FROM {_transactions_q()}"
    with engine.connect() as conn:
        val = conn.execute(text(sql)).scalar()
        return int(val or 0)


def read_master_transaction_ids() -> tuple[int, set[int]]:
    engine = get_engine()
    sql = f"SELECT TransactionID FROM {_transactions_q()}"
    df = pd.read_sql(sql, engine)
    if df.empty:
        return 0, set()
    ids = df["TransactionID"].astype(int)
    return int(ids.max()), set(ids.tolist())


def load_categorical_uniques() -> dict[str, list[str]]:
    engine = get_engine()
    out: dict[str, list[str]] = {}
    for col in _CATEGORICAL_COLS:
        sql = f"SELECT DISTINCT [{col}] AS v FROM {_transactions_q()} WHERE [{col}] IS NOT NULL ORDER BY [{col}]"
        df = pd.read_sql(sql, engine)
        out[col] = df["v"].astype(str).tolist()
    return out


def backup_master() -> tuple[int, datetime]:
    """Snapshot toàn bộ bảng Transactions vào Transactions_Backup."""
    cols_sql = ", ".join(f"[{c}]" for c in COLUMNS)
    sql = f"""
        INSERT INTO {_backup_q()} ({cols_sql})
        SELECT {cols_sql}
        FROM {_transactions_q()}
    """
    engine = get_engine()
    ts = datetime.utcnow()
    with engine.begin() as conn:
        result = conn.execute(text(sql))
    return int(result.rowcount or 0), ts


def validate_and_prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    errors: list[str] = []

    ok, msg = test_connection()
    if not ok:
        errors.append(f"Không kết nối được SQL Server: {msg}")
        return raw, errors

    if raw.empty:
        errors.append("Không có dòng dữ liệu để import.")
        return raw, errors

    raw = raw.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in COLUMNS if c not in raw.columns]
    if missing:
        if missing == ["TransactionID"]:
            raw["TransactionID"] = pd.NA
            missing = []
    if missing:
        errors.append(f"Thiếu cột: {', '.join(missing)}")
        return raw, errors

    extra = [c for c in raw.columns if c not in COLUMNS]
    if extra:
        raw = raw.drop(columns=extra)

    df = raw[COLUMNS].copy()

    numeric_cols = [
        "CustomerID",
        "Amount",
        "BranchLat",
        "BranchLong",
        "CreditCardFees",
        "InsuranceFees",
        "LatePaymentAmount",
        "CustomerScore",
        "MonthlyIncome",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if df[numeric_cols].isna().any().any():
        rows = df[numeric_cols].isna().any(axis=1)
        idx = df.index[rows].tolist()[:15]
        errors.append(f"Một số trường số không hợp lệ (index dòng: {idx}).")

    df["TransactionDate"] = parse_transaction_dates(df["TransactionDate"])
    if df["TransactionDate"].isna().any():
        errors.append(
            "TransactionDate không đọc được — dùng ngày hợp lệ (ví dụ 2025-01-29 hoặc 1/29/2025)."
        )

    if errors:
        return df, errors

    max_id, existing = read_master_transaction_ids()
    tid = pd.to_numeric(df["TransactionID"], errors="coerce")

    auto = tid.isna().all() or tid.isna().any()
    if auto:
        if tid.isna().any() and tid.notna().any():
            errors.append(
                "TransactionID: hoặc bỏ cột / để trống toàn bộ để tự gán, "
                "hoặc điền số nguyên cho mọi dòng."
            )
            return df, errors
        start = max_id + 1
        df["TransactionID"] = list(range(start, start + len(df)))
    else:
        df["TransactionID"] = tid.astype(int)
        if df["TransactionID"].duplicated().any():
            errors.append("TransactionID bị trùng trong file import.")
            return df, errors
        overlap = set(df["TransactionID"]) & existing
        if overlap:
            sample = sorted(overlap)[:15]
            errors.append(f"TransactionID đã tồn tại trong database: {sample}...")
            return df, errors

    return df, errors


def append_to_master(
    df: pd.DataFrame,
    *,
    backup: bool = True,
) -> tuple[int, str, str | None]:
    """
    Insert các dòng đã validate vào dbo.Transactions.
    Returns (số dòng, tên bảng, mô tả backup hoặc None).
    """
    prepared, errors = validate_and_prepare(df)
    if errors:
        raise ValueError("; ".join(errors))

    backup_msg: str | None = None
    if backup and table_row_count() > 0:
        n_bak, ts = backup_master()
        backup_msg = f"{_backup_q()} (+{n_bak} dòng lúc {ts:%Y-%m-%d %H:%M:%S} UTC)"

    engine = get_engine()
    chunk = max(1, 2000 // len(COLUMNS))
    prepared.to_sql(
        transactions_table(),
        engine,
        schema=schema_name(),
        if_exists="append",
        index=False,
        chunksize=chunk,
    )
    return len(prepared), master_table_label(), backup_msg


def read_upload_csv(file_obj) -> pd.DataFrame:
    return pd.read_csv(file_obj)


def import_from_file(
    source,
    filename: str,
    *,
    backup: bool = True,
    use_ai_mapping: bool = False,
    use_ai_extract: bool = False,
    sheet_name: str | int | None = None,
) -> tuple[int, str, str | None, dict, dict[str, str], str]:
    """
  Đọc file đa định dạng → map cột → ghi SQL.
    Returns (n_rows, table, backup_msg, file_meta, column_mapping, map_method).
    """
    from column_mapper import map_to_schema
    from file_importer import load_file

    raw, meta = load_file(
        source,
        filename,
        sheet_name=sheet_name,
        use_ai_extract=use_ai_extract,
    )
    mapped, mapping, method = map_to_schema(raw, use_ai=use_ai_mapping)
    if "TransactionID" not in mapped.columns:
        mapped = mapped.copy()
        mapped["TransactionID"] = pd.NA

    n, table, bak = append_to_master(mapped, backup=backup)
    meta["column_mapping"] = mapping
    meta["map_method"] = method
    return n, table, bak, meta, mapping, method


def load_all_transactions() -> pd.DataFrame:
    """Đọc toàn bộ transactions (dùng cho notebook / kiểm tra)."""
    engine = get_engine()
    sql = f"SELECT {', '.join(f'[{c}]' for c in COLUMNS)} FROM {_transactions_q()}"
    return pd.read_sql(sql, engine)


def save_isolation_output(df: pd.DataFrame) -> int:
    """Ghi kết quả Isolation Forest vào dbo.IsolationOutput (thay isolation_output.csv)."""
    from db_config import isolation_table

    engine = get_engine()
    q = qualified(isolation_table())
    out = df[["TransactionID", "CustomerID", "IsAnomaly", "AnomalyLabel"]].copy()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {q}"))
    out.to_sql(
        isolation_table(),
        engine,
        schema=schema_name(),
        if_exists="append",
        index=False,
        chunksize=max(1, 2000 // 4),
    )
    return len(out)


def save_anomaly_results(df: pd.DataFrame) -> int:
    """Alias tương thích — ghi vào dbo.IsolationOutput."""
    return save_isolation_output(df)


def _samples_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "samples"


def rank_rfm_csv_path() -> Path:
    return _samples_dir() / "RankRFM.csv"


def load_rank_rfm_lookup() -> pd.DataFrame:
    """Đọc bảng tra cứu Segment/Scores giống RankRFM.csv."""
    path = rank_rfm_csv_path()
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    if list(df.columns) != ["Segment", "Scores"]:
        raise ValueError(f"RankRFM.csv phải có cột Segment, Scores — hiện: {list(df.columns)}")
    return df[["Segment", "Scores"]].copy()


def save_rank_rfm_lookup(df: pd.DataFrame | None = None) -> int:
    """Ghi dbo.RankRFM giống hệt RankRFM.csv (Segment, Scores)."""
    from db_config import rfm_table

    out = load_rank_rfm_lookup() if df is None else df[["Segment", "Scores"]].copy()
    engine = get_engine()
    q = qualified(rfm_table())
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {q}"))
    out.to_sql(
        rfm_table(),
        engine,
        schema=schema_name(),
        if_exists="append",
        index=False,
    )
    return len(out)


def save_rank_rfm(df: pd.DataFrame | None = None) -> int:
    """Alias — RankRFM.csv là bảng tra cứu, không phải df_rfm theo khách."""
    return save_rank_rfm_lookup(df)

