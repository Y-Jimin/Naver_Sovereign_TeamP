import json

from app.services.llm_client import chat_completion

_SYSTEM_PROMPT = (
    "너는 한국 영수증 OCR 텍스트에서 실제로 구매한 음식/음료 품목명만 추출하는 도우미야. "
    "매장명, 주소, 사업자번호, 결제수단, 합계/부가세/받은금액 같은 줄은 무시해. "
    "품목의 수량이나 옵션(예: (H), (ICE), 사이즈)은 음식명에서 제거하지 말고 최대한 원문 그대로 유지해. "
    '반드시 JSON 배열만 출력해: [{"name": "품목명", "quantity": 1}, ...] '
    "다른 설명 텍스트는 절대 추가하지 마."
)


async def _try_extract(ocr_text: str) -> list[dict]:
    response = await chat_completion(_SYSTEM_PROMPT, ocr_text, max_tokens=512)
    text = response.strip()
    # 모델이 코드블록으로 감싸는 경우 대비
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("["):]
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return []
    return [item for item in items if isinstance(item, dict) and item.get("name")]


async def extract_food_items(ocr_text: str) -> list[dict]:
    items = await _try_extract(ocr_text)
    if items:
        return items
    # LLM 샘플링 편차로 가끔 빈 배열/깨진 JSON이 나옴 — 한 번 더 시도
    return await _try_extract(ocr_text)
