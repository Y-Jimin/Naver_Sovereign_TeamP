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
    # "receipt": RAG로 매칭됨 (matched_food는 읽기 전용). "label": 영양성분표에서 직접
    # 추출됨, RAG 매칭 없음 — FE에서 matched_food를 사용자가 입력하는 칸으로 띄워야 함.
    source: str = "receipt"


class AnalyzeResponse(BaseModel):
    items: list[NutritionItem]
    total_calories_kcal: float
    raw_ocr_text: str
    comment: str | None = None


class CommentRequest(BaseModel):
    items: list[NutritionItem]


class CommentResponse(BaseModel):
    comment: str | None = None
