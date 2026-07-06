import asyncio

from app.schemas import NutritionItem
from app.services.llm_client import chat_completion
from app.services.rag_store import food_rag_store

_HIGH_CONFIDENCE = 0.85
_MEDIUM_CONFIDENCE = 0.7

_SUMMARY_SYSTEM_PROMPT = (
    "너는 영양 코치야. 아래 품목별 칼로리/영양성분 목록을 보고, "
    "이번 식사의 전체적인 영양 특징과 간단한 조언을 3문장 이내 한국어로 작성해줘. "
    "숫자를 새로 만들어내지 말고 주어진 값만 근거로 말해."
)


async def _match_one(name: str) -> NutritionItem:
    matches = await food_rag_store.search(name, top_k=1)
    if not matches:
        return NutritionItem(receipt_name=name, confidence="low", note="일치하는 음식을 찾지 못함")

    food, score = matches[0]
    if score >= _HIGH_CONFIDENCE:
        confidence, note = "high", None
    elif score >= _MEDIUM_CONFIDENCE:
        confidence, note = "medium", "유사 항목으로 추정된 값"
    else:
        confidence, note = "low", "정확히 일치하는 음식이 없어 가장 유사한 항목으로 추정"

    return NutritionItem(
        receipt_name=name,
        matched_food=food.name,
        calories_kcal=food.calories_kcal,
        carbs_g=food.carbs_g,
        protein_g=food.protein_g,
        fat_g=food.fat_g,
        sodium_mg=food.sodium_mg,
        confidence=confidence,
        note=note,
    )


async def build_nutrition_items(items: list[dict]) -> list[NutritionItem]:
    return list(await asyncio.gather(*(_match_one(item["name"]) for item in items)))


async def summarize_meal(items: list[NutritionItem]) -> str | None:
    matched = [i for i in items if i.calories_kcal is not None]
    if not matched:
        return None
    lines = [
        f"- {i.matched_food}: {i.calories_kcal}kcal, 탄{i.carbs_g}g/단{i.protein_g}g/지{i.fat_g}g/나트륨{i.sodium_mg}mg"
        for i in matched
    ]
    return await chat_completion(_SUMMARY_SYSTEM_PROMPT, "\n".join(lines), max_tokens=256)
