# -*- coding: utf-8 -*-
"""
Import một lần từ CSV master sang SQL Server.

Chạy sau khi đã execute sql/01 và sql/02 trong SSMS (chỉ khi cần import lại từ file CSV):
  python tools/migrate_csv_to_sql.py path\to\file.csv
  python tools/migrate_csv_to_sql.py path\to\file.csv --replace
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db_config import get_engine, qualified, schema_name, test_connection, transactions_table  # noqa: E402
from ingest_core import COLUMNS, parse_transaction_dates  # noqa: E402

def main() -> int:
    p = argparse.ArgumentParser(description="Import file CSV vào SQL Server (dbo.Transactions)")
    p.add_argument("csv_file", type=Path, help="Đường dẫn file CSV cần import")
    p.add_argument("--replace", action="store_true", help="Xóa dữ liệu cũ trong bảng Transactions trước khi import")
    args = p.parse_args()

    ok, msg = test_connection()
    if not ok:
        print(f"Không kết nối SQL: {msg}", file=sys.stderr)
        print("Kiểm tra .env và SSMS (SQL Server đang chạy).", file=sys.stderr)
        return 1

    if not args.csv_file.is_file():
        print(f"Không tìm thấy CSV: {args.csv_file}", file=sys.stderr)
        return 1

    df = pd.read_csv(args.csv_file)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[COLUMNS].copy()
    df["TransactionDate"] = parse_transaction_dates(df["TransactionDate"])

    engine = get_engine()
    q = qualified(transactions_table())

    with engine.begin() as conn:
        if args.replace:
            conn.execute(text(f"TRUNCATE TABLE {q}"))
            print(f"TRUNCATE {q}")

    # SQL Server tối đa ~2100 tham số/câu INSERT → chunksize ≈ 2000/19 cột
    chunk = max(1, 2000 // len(COLUMNS))
    df.to_sql(
        transactions_table(),
        engine,
        schema=schema_name(),
        if_exists="append",
        index=False,
        chunksize=chunk,
    )
    print(f"Imported {len(df)} rows from {args.csv_file} -> {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
