# -*- coding: utf-8 -*-
"""CLI: import file đa định dạng vào dbo.Transactions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db_config import test_connection  # noqa: E402
from file_importer import SUPPORTED_EXTENSIONS  # noqa: E402
from ingest_core import import_from_file  # noqa: E402


def main() -> int:
    exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    p = argparse.ArgumentParser(
        description=f"Import file ({exts}) vào SQL Server dbo.Transactions"
    )
    p.add_argument("file", type=Path, help="Đường dẫn file nguồn")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--ai-map", action="store_true", help="AI map tên cột (Groq/Gemini trong .env)")
    p.add_argument("--ai-extract", action="store_true", help="AI trích xuất bảng từ DOCX/TXT")
    p.add_argument("--sheet", default="0", help="Tên hoặc index sheet Excel (mặc định 0)")
    args = p.parse_args()

    ok, msg = test_connection()
    if not ok:
        print(f"Loi ket noi SQL: {msg}", file=sys.stderr)
        return 3

    if not args.file.is_file():
        print(f"Khong tim thay: {args.file}", file=sys.stderr)
        return 1

    sheet: str | int = int(args.sheet) if str(args.sheet).isdigit() else args.sheet

    try:
        n, table, bak, meta, mapping, method = import_from_file(
            args.file,
            args.file.name,
            backup=not args.no_backup,
            use_ai_mapping=args.ai_map,
            use_ai_extract=args.ai_extract,
            sheet_name=sheet,
        )
    except ValueError as e:
        print(f"Loi validate: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Loi: {e}", file=sys.stderr)
        return 4

    print(f"Format: {meta.get('format')} | rows read: {meta.get('rows')} | map: {method}")
    print(f"Column mapping: {mapping}")
    print(f"Da them {n} dong vao {table}")
    if bak:
        print(f"Backup: {bak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
