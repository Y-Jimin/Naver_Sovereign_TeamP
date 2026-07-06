import uuid

import httpx

from app.config import settings

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30)
    return _client


async def chat_completion(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Call HyperCLOVA X via CLOVA Studio's OpenAI-compatible chat completions
    endpoint and return the assistant message text.

    Reuses one AsyncClient (and its connection pool) across calls instead of
    opening a fresh TCP+TLS connection per request.
    """
    payload = {
        "model": settings.clova_studio_chat_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.clova_studio_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = await _get_client().post(
        f"{settings.clova_studio_api_base_url}/chat/completions", json=payload, headers=headers
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
