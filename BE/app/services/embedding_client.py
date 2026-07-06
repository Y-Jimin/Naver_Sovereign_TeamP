import uuid

import httpx
import numpy as np

from app.config import settings

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30)
    return _client


async def embed_text(text: str) -> np.ndarray:
    """Call CLOVA Studio's OpenAI-compatible embeddings endpoint.

    Reuses one AsyncClient (and its connection pool) across calls instead of
    opening a fresh TCP+TLS connection per request.
    """
    payload = {"model": settings.clova_studio_embedding_model, "input": text}
    headers = {
        "Authorization": f"Bearer {settings.clova_studio_api_key}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = await _get_client().post(
        f"{settings.clova_studio_api_base_url}/embeddings", json=payload, headers=headers
    )
    resp.raise_for_status()
    data = resp.json()
    return np.array(data["data"][0]["embedding"], dtype=np.float32)
