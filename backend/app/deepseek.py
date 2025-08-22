import os
from typing import Dict

import httpx

DEEPSEEK_URL = "https://api.deepseek.com/company"

class DeepSeekError(Exception):
    """Raised when the DeepSeek API cannot provide data."""


def fetch_company_data(query: str) -> Dict:
    """Fetch company data from the DeepSeek API for the given query.

    Parameters
    ----------
    query: str
        The company domain or name to search for.
    """
    headers = {}
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = httpx.get(
            DEEPSEEK_URL, params={"query": query}, headers=headers, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise DeepSeekError("Invalid response from DeepSeek API")
        return data
    except Exception as exc:  # broad to wrap httpx/network errors
        raise DeepSeekError(str(exc)) from exc
