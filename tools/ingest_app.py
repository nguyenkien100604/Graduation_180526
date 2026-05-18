# -*- coding: utf-8 -*-
"""
Streamlit: nhập transaction (tay / file đa định dạng) → SQL Server.

  streamlit run tools/ingest_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from column_mapper import map_to_schema, suggest_column_mapping  # noqa: E402
from db_config import test_connection  # noqa: E402
from file_importer import SUPPORTED_EXTENSIONS, load_file  # noqa: E402
from ingest_core import COLUMNS, append_to_master, load_categorical_uniques, master_table_label, table_row_count  # noqa: E402

st.set_page_config(page_title="Nhập dữ liệu transaction", layout="wide")

_EXT_LIST = sorted(SUPPORTED_EXTENSIONS)
from ai_client import ai_available, ai_provider  # noqa: E402

_HAS_AI = ai_available()


@st.cache_data
def _uniques() -> dict[str, list[str]]:
    try:
        if table_row_count() == 0:
            return {}
        return load_categorical_uniques()
    except Exception:
        return {}


def main() -> None:
    st.title("Nhập dữ liệu transaction")
    st.caption("Hỗ trợ CSV, JSON, XLSX, DOCX, TXT")

    ok, conn_msg = test_connection()
    if not ok:
        st.error(f"Không kết nối SQL Server: {conn_msg}")
        st.stop()

    st.success(f"Đã kết nối: **{conn_msg}**")
    st.info(f"**Bảng:** `{master_table_label()}` — **{table_row_count():,}** dòng")

    backup = st.sidebar.checkbox("Backup vào Transactions_Backup trước khi ghi", value=True)
    use_ai_map = st.sidebar.checkbox(
        "AI map tên cột",
        value=False,
        disabled=not _HAS_AI,
        help="Groq / Gemini — cấu hình trong .env",
    )
    use_ai_extract = st.sidebar.checkbox(
        "AI trích xuất từ văn bản (DOCX/TXT)",
        value=False,
        disabled=not _HAS_AI,
        help="DOCX/TXT mẫu dùng parser cục bộ trước; chỉ bật khi cần AI và còn quota Gemini.",
    )
    if _HAS_AI:
        st.sidebar.caption(f"AI provider: **{ai_provider() or '—'}**")
    else:
        st.sidebar.caption(
            "Thêm API vào `.env` — **free:** [Groq](https://console.groq.com) hoặc "
            "[Google AI Studio](https://aistudio.google.com/apikey)."
        )

    sheet_name = st.sidebar.text_input("Sheet Excel (tên hoặc 0)", value="0")

    tab_manual, tab_file = st.tabs(["Nhập tay", "Import file"])

    with tab_manual:
        _render_manual_tab(backup, _uniques())

    with tab_file:
        _render_file_tab(backup, use_ai_map, use_ai_extract, sheet_name)


def _render_manual_tab(backup: bool, uniques: dict) -> None:
    st.subheader("Form nhập transaction")
    with st.form("manual_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            customer_id = st.number_input("CustomerID", min_value=1, value=1, step=1)
            tdate = st.date_input("Ngày transaction")
            ttime = st.time_input("Giờ", value=pd.Timestamp.now().time())
            amount = st.number_input("Amount", min_value=0.0, value=1000.0, format="%.2f")
        with c2:
            ttype = st.selectbox("TransactionType", uniques.get("TransactionType", ["Deposit", "Withdrawal"]))
            pcat = st.selectbox("ProductCategory", uniques.get("ProductCategory", ["Loan"]))
            psub = st.selectbox("ProductSubcategory", uniques.get("ProductSubcategory", ["Standard"]))
        with c3:
            city = st.selectbox("BranchCity", uniques.get("BranchCity", ["Madrid"]))
            lat = st.number_input("BranchLat", format="%.4f", value=40.4168)
            lon = st.number_input("BranchLong", format="%.4f", value=-3.7038)
            channel = st.selectbox("Channel", uniques.get("Channel", ["Online"]))
            currency = st.selectbox("Currency", uniques.get("Currency", ["EUR", "USD"]))
        c4, c5 = st.columns(2)
        with c4:
            ccf = st.number_input("CreditCardFees", min_value=0.0, value=0.0, format="%.2f")
            ins = st.number_input("InsuranceFees", min_value=0.0, value=0.0, format="%.2f")
            late = st.number_input("LatePaymentAmount", min_value=0.0, value=0.0, format="%.2f")
        with c5:
            score = st.number_input("CustomerScore", min_value=0, max_value=1000, value=600)
            income = st.number_input("MonthlyIncome", min_value=0.0, value=5000.0, format="%.2f")
            seg = st.selectbox("CustomerSegment", uniques.get("CustomerSegment", ["Middle Income Segment"]))
            offer = st.selectbox("RecommendedOffer", uniques.get("RecommendedOffer", ["Mid-tier Savings Booster"]))

        submitted = st.form_submit_button("Ghi SQL Server")

    if submitted:
        row = {
            "TransactionID": pd.NA,
            "CustomerID": int(customer_id),
            "TransactionDate": f"{tdate} {ttime}",
            "TransactionType": ttype,
            "Amount": float(amount),
            "ProductCategory": pcat,
            "ProductSubcategory": psub,
            "BranchCity": city,
            "BranchLat": float(lat),
            "BranchLong": float(lon),
            "Channel": channel,
            "Currency": currency,
            "CreditCardFees": float(ccf),
            "InsuranceFees": float(ins),
            "LatePaymentAmount": float(late),
            "CustomerScore": int(score),
            "MonthlyIncome": float(income),
            "CustomerSegment": seg,
            "RecommendedOffer": offer,
        }
        try:
            n, table, bak = append_to_master(pd.DataFrame([row]), backup=backup)
            st.success(f"Đã thêm {n} dòng vào `{table}`.")
            if bak:
                st.info(f"Backup: {bak}")
            st.cache_data.clear()
        except ValueError as e:
            st.error(str(e))


def _render_file_tab(backup: bool, use_ai_map: bool, use_ai_extract: bool, sheet_name: str) -> None:
    st.subheader("Import file → SQL")
    st.markdown(
        f"**Định dạng:** {', '.join(_EXT_LIST)}  \n"
        "Hệ thống tự nhận delimiter / bảng Word / sheet Excel và **map cột** về schema `Transactions`."
    )

    f = st.file_uploader("Chọn file", type=[e.lstrip(".") for e in _EXT_LIST])
    if f is None:
        sample = pd.DataFrame(columns=[c for c in COLUMNS if c != "TransactionID"])
        st.download_button(
            "Tải template CSV",
            sample.to_csv(index=False).encode("utf-8"),
            file_name="transaction_import_template.csv",
        )
        return

    sheet: str | int | None = 0
    if Path(f.name).suffix.lower() in (".xlsx", ".xls") and sheet_name.strip():
        sheet = int(sheet_name) if sheet_name.strip().isdigit() else sheet_name.strip()

    try:
        raw, meta = load_file(f, f.name, sheet_name=sheet, use_ai_extract=use_ai_extract)
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            st.error(
                "Hết quota AI. Thêm **GROQ_API_KEY** (free tại console.groq.com) và đặt "
                "`AI_PROVIDER=auto` trong `.env`, hoặc tạo key Gemini mới. DOCX mẫu vẫn import được "
                "khi **tắt AI trích xuất** (parser cục bộ)."
            )
        else:
            st.error(f"Không đọc được file: {e}")
        return

    extract_via = meta.get("extract", "file")
    hint = f" ({extract_via})" if extract_via else ""
    st.success(f"Đã đọc **{meta.get('rows', 0)}** dòng{hint} — {meta.get('format', '')}")
    mapped, mapping, method = map_to_schema(raw, use_ai=use_ai_map)
    suggested = suggest_column_mapping(list(raw.columns))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Cột file gốc**")
        st.dataframe(raw.head(20), use_container_width=True)
    with c2:
        st.markdown(f"**Sau map cột** ({method})")
        st.json(mapping)
        st.dataframe(mapped.head(20), use_container_width=True)

    missing = [c for c in COLUMNS if c not in mapped.columns and c != "TransactionID"]
    if missing:
        st.warning(f"Thiếu cột (có thể cần bật AI hoặc đổi tên cột trong file): **{', '.join(missing)}**")

    if st.button("Ghi vào SQL Server", type="primary"):
        try:
            out = mapped.copy()
            if "TransactionID" not in out.columns:
                out["TransactionID"] = pd.NA
            n, table, bak = append_to_master(out, backup=backup)
            st.success(f"Đã thêm **{n}** dòng vào `{table}`.")
            if bak:
                st.info(f"Backup: {bak}")
            st.cache_data.clear()
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Lỗi: {e}")


if __name__ == "__main__":
    main()
