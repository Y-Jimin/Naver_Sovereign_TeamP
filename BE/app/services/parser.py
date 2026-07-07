import json
import re

from app.services.llm_client import chat_completion

# OCR 원문의 "00g"처럼 값이 없는 자리를 모델이 그대로 숫자로 옮기면 "00"이 되어
# JSON 파싱이 깨진다 (선행 0은 유효한 JSON 숫자가 아님) — 파싱 전에 보정한다.
_LEADING_ZERO_RE = re.compile(r"(?<![\d.])0+(\d)")


def _fix_leading_zeros(text: str) -> str:
    return _LEADING_ZERO_RE.sub(r"\1", text)

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


_CLASSIFY_SYSTEM_PROMPT = (
    "너는 OCR로 추출한 텍스트가 '영수증'인지 '영양성분표'인지 구분하는 도우미야. "
    "영수증은 매장명/주소/사업자번호/품목별 가격/합계/카드 승인번호 같은 내용이 있어. "
    "영양성분표는 '영양정보', '1회 제공량', '총 내용량', '1일 영양성분 기준치', "
    "'탄수화물', '나트륨', '포화지방' 같은 표 형태 항목이 나열돼 있어. "
    "다른 설명 없이 receipt 또는 nutrition_label 중 하나만 정확히 출력해."
)


async def classify_document(ocr_text: str) -> str:
    response = await chat_completion(_CLASSIFY_SYSTEM_PROMPT, ocr_text, max_tokens=16)
    return "nutrition_label" if "nutrition_label" in response else "receipt"


_NUTRITION_LABEL_SYSTEM_PROMPT = (
    "너는 영양성분표 OCR 텍스트에서 값을 추출하는 도우미야. "
    "반드시 아래 형식의 JSON 객체만 출력해, 다른 설명은 절대 추가하지 마: "
    '{"calories_kcal": number|null, "carbs_g": number|null, "protein_g": number|null, '
    '"fat_g": number|null, "sodium_mg": number|null, "reference_grams": number|null} '
    "reference_grams는 위 영양성분 값들이 몇 g(또는 ml) 기준인지야 "
    "(예: '총 내용량 250g', '1회 제공량 30g'). 기준량을 텍스트에서 찾을 수 없으면 null로 둬. "
    "값을 아예 찾을 수 없거나 '00'처럼 채워지지 않은 자리는 null로 둬. "
    "숫자에 단위나 콤마, 불필요한 선행 0을 붙이지 마 (0으로만, '00' 금지)."
)


async def extract_nutrition_facts(ocr_text: str) -> dict | None:
    response = await chat_completion(_NUTRITION_LABEL_SYSTEM_PROMPT, ocr_text, max_tokens=256)
    text = response.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    text = _fix_leading_zeros(text)
    try:
        facts = json.loads(text)
    except json.JSONDecodeError:
        return None
    return facts if isinstance(facts, dict) else None
