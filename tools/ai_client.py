# -*- coding: utf-8 -*-
"""AI client: Groq (free), Google Gemini, OpenAI — đọc từ .env."""

from __future__ import annotations

import json
import os
import re
from typing import Any

# Thứ tự mặc định khi AI_PROVIDER=auto (ưu tiên free tier ổn định)
_DEFAULT_PROVIDER_ORDER = ("groq", "google", "openai")


class AIQuotaError(Exception):
    """Hết quota / rate limit API AI."""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        from pathlib import Path

        p = Path(__file__).resolve().parents[1] / ".env"
        if p.is_file():
            load_dotenv(p)
    except ImportError:
        pass


_load_dotenv()


def groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def google_api_key() -> str:
    return (
        os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_GENAI_API_KEY", "").strip()
    )


def openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _provider_has_key(name: str) -> bool:
    if name == "groq":
        return bool(groq_api_key())
    if name == "google":
        return bool(google_api_key())
    if name == "openai":
        return bool(openai_api_key())
    return False


def configured_providers() -> list[str]:
    return [p for p in _DEFAULT_PROVIDER_ORDER if _provider_has_key(p)]


def ai_available() -> bool:
    return bool(configured_providers())


def _provider_order() -> list[str]:
    pref = os.getenv("AI_PROVIDER", "auto").strip().lower()
    if pref in ("groq", "google", "openai"):
        return [pref] if _provider_has_key(pref) else []
    if pref == "auto":
        custom = os.getenv("AI_PROVIDER_ORDER", "").strip()
        if custom:
            names = [x.strip().lower() for x in custom.split(",") if x.strip()]
        else:
            names = list(_DEFAULT_PROVIDER_ORDER)
        return [p for p in names if p in _DEFAULT_PROVIDER_ORDER and _provider_has_key(p)]
    return []


def ai_provider() -> str | None:
    """Provider sẽ dùng trước (hoặc chuỗi auto)."""
    order = _provider_order()
    if not order:
        return None
    if len(order) == 1:
        return order[0]
    return "auto → " + ", ".join(order)


def _gemini_model_list() -> list[str]:
    primary = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite").strip()
    extra = os.getenv("GEMINI_MODEL_FALLBACKS", "gemini-1.5-flash-8b,gemini-2.0-flash-lite")
    models = [primary] + [m.strip() for m in extra.split(",") if m.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for m in models:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _is_quota_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "429" in msg
        or "quota" in msg
        or "resourceexhausted" in msg
        or "rate limit" in msg
        or "insufficient_quota" in msg
    )


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _groq_generate(system: str, user: str) -> str:
    key = groq_api_key()
    if not key:
        raise AIQuotaError("Chưa cấu hình GROQ_API_KEY — lấy free tại https://console.groq.com")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise AIQuotaError("Thiếu thư viện: pip install openai") from e

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        if _is_quota_error(e):
            raise AIQuotaError("Đã hết quota Groq — đợi vài phút hoặc đổi GROQ_MODEL.") from e
        raise


def _gemini_generate(system: str, user: str) -> str:
    key = google_api_key()
    if not key:
        raise AIQuotaError("Chưa cấu hình GOOGLE_API_KEY trong .env")

    try:
        import google.generativeai as genai
    except ImportError as e:
        raise AIQuotaError("Thiếu thư viện: pip install google-generativeai") from e

    genai.configure(api_key=key)
    last_err: BaseException | None = None

    for model_name in _gemini_model_list():
        try:
            model = genai.GenerativeModel(model_name, system_instruction=system)
            resp = model.generate_content(user, generation_config={"temperature": 0})
            text = (resp.text or "").strip()
            if text:
                return text
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                continue
            raise

    if last_err and _is_quota_error(last_err):
        raise AIQuotaError(
            "Hết quota Gemini. Tạo key mới tại https://aistudio.google.com/apikey, "
            "đổi GEMINI_MODEL=gemini-2.0-flash-lite, hoặc dùng GROQ_API_KEY (free)."
        ) from last_err
    if last_err:
        raise last_err
    raise AIQuotaError("Gemini không trả về kết quả.")


def _openai_generate(system: str, user: str) -> str:
    key = openai_api_key()
    if not key:
        raise AIQuotaError("Chưa cấu hình OPENAI_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise AIQuotaError("Thiếu thư viện: pip install openai") from e

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=key)
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        if _is_quota_error(e):
            raise AIQuotaError("Đã hết quota OpenAI.") from e
        raise


def _generate_with_provider(provider: str, system: str, user: str) -> str:
    if provider == "groq":
        return _groq_generate(system, user)
    if provider == "google":
        return _gemini_generate(system, user)
    if provider == "openai":
        return _openai_generate(system, user)
    raise AIQuotaError(f"Provider không hỗ trợ: {provider}")


def ai_generate(system: str, user: str) -> tuple[str | None, str | None]:
    """
    Gọi AI theo AI_PROVIDER / AI_PROVIDER_ORDER.
    Khi auto: thử lần lượt; nếu provider A hết quota → chuyển sang B.
    """
    order = _provider_order()
    if not order:
        return None, None

    last_quota: AIQuotaError | None = None
    for name in order:
        try:
            text = _generate_with_provider(name, system, user)
            if text:
                return text, name
        except AIQuotaError as e:
            last_quota = e
            continue

    if last_quota:
        raise last_quota
    return None, None


def ai_json_object(system: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        user = json.dumps(payload, ensure_ascii=False, default=str)
        text, _ = ai_generate(system, user)
        if not text:
            return None
        data = json.loads(_strip_json_fence(text))
        return data if isinstance(data, dict) else None
    except AIQuotaError:
        raise
    except (json.JSONDecodeError, Exception):
        return None


def ai_json_array(system: str, user_text: str) -> list[dict[str, Any]] | None:
    try:
        text, _ = ai_generate(system, user_text)
        if not text:
            return None
        data = json.loads(_strip_json_fence(text))
        return data if isinstance(data, list) else None
    except AIQuotaError:
        raise
    except (json.JSONDecodeError, Exception):
        return None
