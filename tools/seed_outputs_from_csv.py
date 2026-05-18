# -*- coding: utf-8 -*-
"""
Nạp dbo.RankRFM và dbo.IsolationOutput từ file CSV mẫu (giống dataset/output cũ).

  python tools/seed_outputs_from_csv.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db_config import test_connection  # noqa: E402
from ingest_core import save_isolation_output, save_rank_rfm_lookup  # noqa: E402
from ingest_core import isolation_output_csv_path, load_rank_rfm_lookup, rank_rfm_csv_path  # noqa: E402
import pandas as pd  # noqa: E402


def main() -> int:
    ok, msg = test_connection()
    if not ok:
        print(f"SQL error: {msg}", file=sys.stderr)
        return 1

    rfm = load_rank_rfm_lookup()
    n_rfm = save_rank_rfm_lookup(rfm)
    print(f"RankRFM: {n_rfm} rows from {rank_rfm_csv_path()}")

    iso_path = isolation_output_csv_path()
    iso = pd.read_csv(iso_path)
    n_iso = save_isolation_output(iso)
    print(f"IsolationOutput: {n_iso} rows from {iso_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
