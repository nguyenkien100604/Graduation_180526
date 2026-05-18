# -*- coding: utf-8 -*-
"""Ánh xạ cột file nguồn → schema Transactions (fuzzy + AI tùy chọn)."""

from __future__ import annotations

import json
import os
import re
from difflib import get_close_matches
from typing import Any

import pandas as pd

from ingest_core import COLUMNS

# Gợi ý tên cột thường gặp (EN / VI / viết tắt)
COLUMN_ALIASES: dict[str, list[str]] = {
    "TransactionID": ["transaction_id", "txn_id", "id", "ma_gd", "magiaodich"],
    "CustomerID": ["customer_id", "cust_id", "client_id", "ma_kh", "makhachhang", "user_id"],
    "TransactionDate": ["transaction_date", "txn_date", "date", "datetime", "ngay_gd", "thoi_gian"],
    "TransactionType": ["transaction_type", "type", "loai_gd", "loai"],
    "Amount": ["amount", "so_tien", "value", "transaction_amount", "tien"],
    "ProductCategory": ["product_category", "category", "nhom_sp", "loai_sp"],
    "ProductSubcategory": ["product_subcategory", "subcategory", "phan_loai"],
    "BranchCity": ["branch_city", "city", "thanh_pho", "branch"],
    "BranchLat": ["branch_lat", "latitude", "lat", "vi_do"],
    "BranchLong": ["branch_long", "longitude", "lon", "lng", "kinh_do"],
    "Channel": ["channel", "kenh", "payment_channel"],
    "Currency": ["currency", "tien_te", "curr"],
    "CreditCardFees": ["credit_card_fees", "card_fee", "phi_the"],
    "InsuranceFees": ["insurance_fees", "insurance_fee", "phi_bh"],
    "LatePaymentAmount": ["late_payment_amount", "late_fee", "phi_tre"],
    "CustomerScore": ["customer_score", "score", "diem_kh"],
    "MonthlyIncome": ["monthly_income", "income", "thu_nhap"],
    "CustomerSegment": ["customer_segment", "segment", "phan_khuc"],
    "RecommendedOffer": ["recommended_offer", "offer", "goi_y"],
}


def _normalize_name(name: str) -> str:
    s = str(name).strip().lower()
    s = re.sub(r"[^\w]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")


def _build_alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        lookup[_normalize_name(target)] = target
        for a in aliases:
            lookup[_normalize_name(a)] = target
    return lookup


_ALIAS_LOOKUP = _build_alias_lookup()


def suggest_column_mapping(source_columns: list[str]) -> dict[str, str]:
    """source_col -> target_col (chỉ các cột map được)."""
    mapping: dict[str, str] = {}
    targets = list(COLUMNS)
    targets_norm = {_normalize_name(t): t for t in targets}

    for src in source_columns:
        src_norm = _normalize_name(src)
        if src_norm in _ALIAS_LOOKUP:
            mapping[src] = _ALIAS_LOOKUP[src_norm]
            continue
        if src_norm in targets_norm:
            mapping[src] = targets_norm[src_norm]
            continue
        # Fuzzy trên tên chuẩn hóa
        pool = list(_ALIAS_LOOKUP.keys()) + list(targets_norm.keys())
        match = get_close_matches(src_norm, pool, n=1, cutoff=0.72)
        if match:
            key = match[0]
            mapping[src] = _ALIAS_LOOKUP.get(key) or targets_norm.get(key)
    return mapping


def apply_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    out = df.rename(columns=mapping)
    # Giữ cột đích đã map; bỏ cột thừa sẽ do validate_and_prepare xử lý
    return out


def ai_suggest_mapping(
    source_columns: list[str],
    sample_rows: list[dict[str, Any]],
) -> dict[str, str] | None:
    """Gọi Gemini (Google AI Studio) hoặc OpenAI để gợi ý map cột."""
    from ai_client import AIQuotaError, ai_json_object

    try:
        data = ai_json_object(
            "Map source columns to the banking transaction schema. Reply with valid JSON only.",
            {
                "task": "Map source columns to banking transaction schema.",
                "target_columns": COLUMNS,
                "source_columns": source_columns,
                "sample_rows": sample_rows[:3],
                "rules": [
                    'Return JSON: {"SourceCol": "TargetCol", ...}',
                    "TargetCol must be one of target_columns",
                    "TransactionID may be omitted if absent",
                ],
            },
        )
    except AIQuotaError:
        return None
    if not data:
        return None
    valid = set(COLUMNS)
    return {str(k): str(v) for k, v in data.items() if str(v) in valid}


def map_to_schema(
    df: pd.DataFrame,
    *,
    use_ai: bool = False,
) -> tuple[pd.DataFrame, dict[str, str], str]:
    """
    Chuẩn hóa tên cột về schema Transactions.
    Returns (dataframe, mapping dict, method_label).
    """
    if df.empty:
        return df, {}, "empty"

    mapping = suggest_column_mapping(list(df.columns))
    method = "fuzzy"

    if use_ai:
        try:
            sample = df.head(5).to_dict(orient="records")
            ai_map = ai_suggest_mapping(list(df.columns), sample)
            if ai_map:
                mapping.update({k: v for k, v in ai_map.items() if k not in mapping})
                method = "fuzzy+ai"
        except Exception:
            pass  # hết quota → chỉ dùng fuzzy

    mapped = apply_column_mapping(df, mapping)
    return mapped, mapping, method
