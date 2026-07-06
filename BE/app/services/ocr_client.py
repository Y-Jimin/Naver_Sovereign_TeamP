import base64
import time
import uuid

import httpx

from app.config import settings


async def run_ocr(image_bytes: bytes, image_format: str = "jpg") -> str:
    """Call CLOVA OCR (General/Receipt domain) and return the concatenated
    text of every detected field, in reading order.

    NOTE: the request/response shape below matches CLOVA OCR's General
    domain as of this writing. If your NCP console shows a different
    schema for your domain (e.g. a dedicated Receipt template with
    structured item fields), adjust `_extract_text` to read those fields
    directly instead of falling back to plain text concatenation.
    """
    payload = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "images": [
            {
                "format": image_format,
                "name": "receipt",
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            }
        ],
    }
    headers = {
        "X-OCR-SECRET": settings.clova_ocr_secret_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(settings.clova_ocr_invoke_url, json=payload, headers=headers)
        resp.raise_for_status()
        return _extract_text(resp.json())


def _extract_text(ocr_response: dict) -> str:
    lines = []
    for image in ocr_response.get("images", []):
        for field in image.get("fields", []):
            text = field.get("inferText", "")
            if text:
                lines.append(text)
            if field.get("lineBreak"):
                lines.append("\n")
    return " ".join(lines).replace(" \n ", "\n").strip()
