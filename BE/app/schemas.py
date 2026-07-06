from pydantic import BaseModel


class NutritionItem(BaseModel):
    receipt_name: str
    matched_food: str | None = None
    calories_kcal: float | None = None
    carbs_g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None
    confidence: str = "low"
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
