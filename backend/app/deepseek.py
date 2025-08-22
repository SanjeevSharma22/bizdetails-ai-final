import os
from typing import Dict, Optional

import httpx

DEEPSEEK_URL = "https://api.deepseek.com"

# Prompt used for requesting company enrichment data from the DeepSeek API.
DEEPSEEK_PROMPT = (
    "You are an expert at information retrieval and data enrichment. Your task is to "
    "provide comprehensive and accurate details about a company based on its name, "
    "domain, or LinkedIn URL.\n\n"
    "Input\n"
    "name: The common name of the company (e.g., \"Google\", \"Microsoft\", \"Salesforce\").\n"
    "domain: The primary domain of the company (e.g., \"https://www.google.com/search?q=google.com\", "
    "\"microsoft.com\", \"salesforce.com\").\n"
    "linkedin_url: The URL of the company's official LinkedIn page (e.g., "
    "\"https://www.linkedin.com/company/google\", \"https://www.linkedin.com/company/microsoft\").\n\n"
    "Output Format\n"
    "Your output must be a single JSON object with the following keys. Ensure the data "
    "is as detailed and accurate as possible. If a piece of information cannot be "
    "found, the key's value should be null or an empty array [].\n\n"
    "JSON\n\n"
    "{\n"
    "  \"name\": null,\n"
    "  \"domain\": null,\n"
    "  \"countries\": [],\n"
    "  \"hq\": null,\n"
    "  \"industry\": null,\n"
    "  \"subindustries\": [],\n"
    "  \"keywords_cntxt\": [],\n"
    "  \"size\": null,\n"
    "  \"linkedin_url\": null,\n"
    "  \"slug\": null,\n"
    "  \"original_name\": null,\n"
    "  \"legal_name\": null\n"
    "}\n\n"
    "Key Definitions & Requirements\n"
    "name: The common or trade name of the company as it is widely known.\n\n"
    "domain: The primary domain of the company's website.\n\n"
    "countries: An array of strings. List all countries where the company has physical "
    "offices or a significant operational presence. Do not include countries where the "
    "company only sells products.\n\n"
    "hq: A string. The country where the company's headquarters is located.\n\n"
    "industry: A string. The primary industry the company belongs to (e.g., \"Information "
    "Technology and Services\", \"Financial Services\", \"Automotive\").\n\n"
    "subindustries: An array of strings. A list of specific sub-industries or sectors "
    "the company operates within (e.g., \"SaaS\", \"Cloud Computing\", \"Artificial Intelligence\").\n\n"
    "keywords_cntxt: An array of strings. A list of the company's official specialties "
    "or keywords as listed on its LinkedIn page or official website.\n\n"
    "size: A string. The employee size range of the company as of the most recent data "
    "available. Use a standard format like \"1001-5000 employees\" or \"10,000+ employees\".\n\n"
    "linkedin_url: A string. The complete and correct URL of the company's official LinkedIn "
    "page.\n\n"
    "slug: A string. The unique identifier used in the company's LinkedIn URL (e.g., for "
    "\"https://www.linkedin.com/company/google\", the slug is \"google\").\n\n"
    "original_name: A string. The common name of the company. This may be the same as the "
    "legal name.\n\n"
    "legal_name: A string. The formal, registered legal name of the company. This may "
    "differ from the original name (e.g., \"Alphabet Inc.\" for \"Google\").\n\n"
    "Constraint Checklist & Instructions\n"
    "You must use the provided JSON structure for your output.\n\n"
    "Prioritize data from the official LinkedIn page, the company's official website, "
    "and other reputable business data sources.\n\n"
    "If multiple names or domains are provided, use them to cross-reference and ensure "
    "accuracy.\n\n"
    "Do not guess or hallucinate information. If data is not available, return null or [].\n\n"
    "Ensure that the linkedin_url and slug are correctly extracted from the LinkedIn profile.\n\n"
    "All data provided must be as current as possible.\n\n"
    "Do not include any conversational text or explanations outside of the JSON output."
)


class DeepSeekError(Exception):
    """Raised when the DeepSeek API cannot provide data."""


def fetch_company_data(
    name: Optional[str] = None,
    domain: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> Dict:
    """Fetch company data from the DeepSeek API.

    Parameters
    ----------
    name: Optional[str]
        Common or trade name of the company.
    domain: Optional[str]
        Primary domain of the company.
    linkedin_url: Optional[str]
        LinkedIn profile URL of the company.
    """
    headers = {}
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": DEEPSEEK_PROMPT,
        "name": name,
        "domain": domain,
        "linkedin_url": linkedin_url,
    }

    try:
        resp = httpx.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise DeepSeekError("Invalid response from DeepSeek API")
        return data
    except Exception as exc:  # broad to wrap httpx/network errors
        raise DeepSeekError(str(exc)) from exc
