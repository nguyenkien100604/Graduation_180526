# -*- coding: utf-8 -*-
"""Trích xuất transaction từ văn bản tự do (không cần AI) — fallback khi hết quota Gemini."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _num(s: str) -> float:
    s = str(s).strip().rstrip(".")
    if re.search(r"\d+\.\d{3},\d+", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.search(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):
        s = re.sub(r"\.(?=\d{3}\b)", "", s).replace(",", ".")
    else:
        s = s.replace(",", "")
    m = re.search(r"-?[\d.]+", s.replace(" ", ""))
    return float(m.group().rstrip(".")) if m else 0.0


def _float_or(default: float, s: str | None) -> float:
    if not s:
        return default
    try:
        return _num(s)
    except ValueError:
        return default


def _find(patterns: list[str], text: str, flags: int = re.I) -> str | None:
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return m.group(1).strip()
    return None


def parse_transaction_block(block: str) -> dict[str, Any] | None:
    """Parse một đoạn mô tả 1 giao dịch (tiếng Việt / Anh)."""
    if len(block.strip()) < 40:
        return None

    cid = _find(
        [
            r"Khach hang(?:\s+so)?\s+(\d+)",
            r"Khach hang\s+(\d+)",
            r"customer\s+(\d+)",
            r"cho\s+customer\s+(\d+)",
            r"ma_kh[:\s]+(\d+)",
        ],
        block,
    )
    if not cid:
        return None

    tdate = _find(
        [
            r"ngay\s+(\d{1,2}/\d{1,2}/\d{4}(?:\s+luc\s+\d{1,2}:\d{2}(?::\d{2})?)?)",
            r"ngay\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})",
            r"vao\s+ngay\s+(\d{1,2}/\d{1,2}/\d{4}[^.\n]*)",
            r"vao\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})",
            r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2})",
        ],
        block,
    ) or _find([r"ngay\s+(\d{1,2}/\d{2}/\d{4}[^.\n]*)"], block)

    ttype = _find(
        [
            r"\((Card Payment|Withdrawal|Deposit|Transfer|Fee)\)",
            r"(Card Payment|Withdrawal|Deposit|Transfer|Fee)",
        ],
        block,
    )

    amount = _find(
        [
            r"so tien\s+([\d.,]+)",
            r"tong\s+([\d.,]+)",
            r"\)\s+([\d.,]+)\s*(?:EUR|USD)",
            r"[\u2014\-]\s*([\d.,]+)\s*(?:EUR|USD)",
            r"([\d.,]+)\s*(?:EUR|USD)",
        ],
        block,
    )

    currency = "EUR"
    if re.search(r"\bUSD\b", block, re.I):
        currency = "USD"

    pcat = _find([r"loai san pham:\s*([^/\n]+)", r"category\s+([^/\n]+)", r"(Checking Account|Mortgage|Loan|Credit Card|Savings Account|Insurance)"], block)
    psub = _find([r"/\s*(\w+)\.", r"subcategory\s+(\w+)", r"(Gold|Platinum|Standard)"], block)

    city = _find([r"Chi nhanh tai\s+(\w+)", r"Thanh pho\s+(\w+)", r"tai\s+(\w+)\s*\(", r"(Seville|Malaga|Madrid|Valencia|Barcelona|Murcia|Bilbao|Zaragoza)"], block)

    lat = _find([r"lat(?:itude)?\s*([\d.]+)", r"\(([\d.]+),\s*-?[\d.]+\)"], block)
    lon = _find(
        [
            r"long(?:itude)?\s*(-?[\d.]+)",
            r"BranchLong\s*(-?[\d.]+)",
            r"lat\s+[\d.]+,\s*long\s+(-?[\d.]+)",
            r"\([\d.]+,\s*(-?[\d.]+)\)",
        ],
        block,
    )

    channel = _find([r"Kenh:\s*(\w+)", r"Channel\s+(\w+)", r"qua\s+(\w+)", r"Giao dich qua\s+(\w+)"], block)
    channel = (channel or "Online").capitalize()
    if channel.lower() == "mobile":
        channel = "Mobile"

    ccf = _find([r"Phi the:\s*([\d.,]+)", r"card\s*([\d.,]+)", r"card_fee[:\s]+([\d.,]+)"], block) or "0"
    ins = _find([r"Phi bao hiem\s*([\d.,]+)", r"insurance\s*([\d.,]+)", r"Phi BH[:\s]+([\d.,]+)"], block) or "0"
    late = _find([r"Phat tre[:\s]+([\d.,]+)", r"late[:\s]+([\d.,]+)", r"tre\s+([\d.,]+)"], block) or "0"

    score = _find([r"Diem(?:\s+khach hang)?[:\s]+(\d+)", r"Score[:\s]+(\d+)", r"CustomerScore[:\s]+(\d+)"], block) or "600"
    income = _find([r"Thu nhap(?:\s+hang thang)?[:\s]+([\d.,]+)", r"Income[:\s]+([\d.,]+)", r"MonthlyIncome[:\s]+([\d.,]+)"], block) or "5000"

    seg = _find(
        [r"Phan khuc:\s*([^.]+)", r"Segment[:\s]*([^.]+)", r"(Middle Income Segment|Low Income Segment|High Income Segment)"],
        block,
    )
    offer = _find([r"Goi y:\s*([^.]+)", r"Offer:\s*([^.]+)", r"De xuat:\s*([^.]+)", r"RecommendedOffer[:\s]*([^.]+)"], block)

    if not tdate or not amount:
        return None

    return {
        "CustomerID": int(cid),
        "TransactionDate": tdate.replace(" luc ", " "),
        "TransactionType": ttype or "Deposit",
        "Amount": _num(amount),
        "ProductCategory": (pcat or "Checking Account").strip(),
        "ProductSubcategory": (psub or "Standard").strip(),
        "BranchCity": (city or "Madrid").strip(),
        "BranchLat": _float_or(40.4168, lat),
        "BranchLong": _float_or(-3.7038, lon),
        "Channel": channel,
        "Currency": currency,
        "CreditCardFees": _num(ccf),
        "InsuranceFees": _num(ins),
        "LatePaymentAmount": _num(late),
        "CustomerScore": int(float(score)),
        "MonthlyIncome": _num(income),
        "CustomerSegment": (seg or "Middle Income Segment").strip().rstrip("."),
        "RecommendedOffer": (offer or "Mid-tier Savings Booster").strip().rstrip("."),
    }


def extract_transactions_from_text(text: str) -> pd.DataFrame:
    """Tách nhiều giao dịch từ văn bản dài."""
    blocks = re.split(r"(?=Giao dich\s+\d+\s*:)", text, flags=re.I)
    rows: list[dict[str, Any]] = []
    for block in blocks:
        row = parse_transaction_block(block)
        if row:
            rows.append(row)
    if not rows:
        row = parse_transaction_block(text)
        if row:
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)
