from __future__ import annotations

"""Utility functions for retrieving company data from the DeepSeek API."""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

# ---------------------------------------------------------------------------
# Configuration

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_PATH = os.getenv("DEEPSEEK_PATH", "/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
REQUEST_TIMEOUT_SECS = float(os.getenv("DEEPSEEK_TIMEOUT_SECS", "30"))

# Prompt instructing the model to output strictly the expected JSON shape.
DEEPSEEK_SYSTEM_PROMPT = (
    "You are an information-retrieval and data-enrichment engine. "
    "Given optional company name, domain, and LinkedIn URL, return a SINGLE JSON object "
    "with these keys only and nothing else (no prose):\n\n"
    "{\n"
    '  "name": null,\n'
    '  "domain": null,\n'
    '  "countries": [],\n'
    '  "hq": null,\n'
    '  "industry": null,\n'
    '  "subindustries": [],\n'
    '  "keywords_cntxt": [],\n'
    '  "size": null,\n'
    '  "linkedin_url": null,\n'
    '  "slug": null,\n'
    '  "original_name": null,\n'
    '  "legal_name": null\n'
    "}\n\n"
    "Rules: If unknown, use null or []. Do not include any text outside JSON. "
    "Prefer official LinkedIn and company site. Ensure linkedin_url and slug are correct."
)

DEEPSEEK_USER_TEMPLATE = (
    "Input:\n"
    "name: {name}\n"
    "domain: {domain}\n"
    "linkedin_url: {linkedin_url}\n"
)


# ---------------------------------------------------------------------------
# Errors


class DeepSeekError(Exception):
    """Raised when the DeepSeek API cannot provide usable data."""


@dataclass
class DeepSeekHTTPError(DeepSeekError):
    status_code: int
    body: str


# ---------------------------------------------------------------------------
# Helpers


def _require_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekError("DEEPSEEK_API_KEY is not set")
    return api_key


def _make_client() -> httpx.Client:
    return httpx.Client(base_url=DEEPSEEK_BASE_URL, timeout=REQUEST_TIMEOUT_SECS)


def _build_payload(
    name: Optional[str], domain: Optional[str], linkedin_url: Optional[str]
) -> Dict[str, Any]:
    user_content = DEEPSEEK_USER_TEMPLATE.format(
        name=name or "null",
        domain=domain or "null",
        linkedin_url=linkedin_url or "null",
    )
    return {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }


def _parse_response_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to parse various expected DeepSeek response shapes."""
    try:
        choices = payload.get("choices")
        if choices:
            content = choices[0]["message"]["content"]
            return json.loads(content)
    except Exception:
        pass

    data_obj = payload.get("data")
    if isinstance(data_obj, dict):
        return data_obj

    expected_keys = {
        "name",
        "domain",
        "countries",
        "hq",
        "industry",
        "subindustries",
        "keywords_cntxt",
        "size",
        "linkedin_url",
        "slug",
        "original_name",
        "legal_name",
    }
    if isinstance(payload, dict) and expected_keys.issubset(payload.keys()):
        return payload

    raise DeepSeekError("Unable to parse DeepSeek response into expected JSON object")


def _validate_shape(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required keys exist with appropriate types, coercing when necessary."""
    schema = {
        "name": (str, type(None)),
        "domain": (str, type(None)),
        "countries": (list,),
        "hq": (str, type(None)),
        "industry": (str, type(None)),
        "subindustries": (list,),
        "keywords_cntxt": (list,),
        "size": (str, type(None)),
        "linkedin_url": (str, type(None)),
        "slug": (str, type(None)),
        "original_name": (str, type(None)),
        "legal_name": (str, type(None)),
    }
    fixed: Dict[str, Any] = {}
    for key, types in schema.items():
        val = obj.get(key)
        if key in {"countries", "subindustries", "keywords_cntxt"}:
            if not isinstance(val, list):
                val = [] if val in (None, "") else [val]
        else:
            if not isinstance(val, types):
                val = None if val in ("", []) else str(val) if val is not None else None
        fixed[key] = val
    return fixed


# ---------------------------------------------------------------------------
# Public API


def fetch_company_data(
    name: Optional[str] = None,
    domain: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch company data from the DeepSeek API and return a normalized dict."""

    api_key = _require_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(name, domain, linkedin_url)

    backoffs = (0.5, 1.0, 2.0)
    last_exc: Optional[Exception] = None

    with _make_client() as client:
        for backoff in (*backoffs, None):
            try:
                resp = client.post(DEEPSEEK_PATH, json=payload, headers=headers)
                if resp.status_code >= 400:
                    raise DeepSeekHTTPError(resp.status_code, resp.text)
                parsed = _parse_response_json(resp.json())
                return _validate_shape(parsed)
            except DeepSeekHTTPError:
                raise
            except (httpx.HTTPError, json.JSONDecodeError, DeepSeekError) as exc:
                last_exc = exc
                if backoff is None:
                    break
                try:
                    import time

                    time.sleep(backoff)
                except Exception:
                    pass

    raise DeepSeekError(f"DeepSeek request failed after retries: {last_exc!s}")


__all__ = [
    "DeepSeekError",
    "DeepSeekHTTPError",
    "fetch_company_data",
]

