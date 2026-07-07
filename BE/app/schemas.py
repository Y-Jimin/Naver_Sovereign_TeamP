from pydantic import BaseModel


class NutritionItem(BaseModel):
    receipt_name: str
    matched_food: str | None = None
    # 아래 5개 값은 매칭된 음식의 100g(또는 100ml) 기준값. 실제 섭취량은 FE에서
    # 사용자가 입력한 g으로 비례 계산한다 (DB가 전부 100g/100ml 기준이라 안전한 가정).
    calories_kcal: float | None = None
    carbs_g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None
    confidence: str = "low"
    similarity: float | None = None
    note: str | None = None


class AnalyzeResponse(BaseModel):
    items: list[NutritionItem]
    total_calories_kcal: float
    raw_ocr_text: str
    comment: str | None = None


class CommentRequest(BaseModel):
    items: list[NutritionItem]


class CommentResponse(BaseModel):
    comment: str | None = None
