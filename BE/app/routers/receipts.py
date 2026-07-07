from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import AnalyzeResponse, CommentRequest, CommentResponse
from app.services import ocr_client, parser
from app.services.nutrition_analyzer import build_nutrition_items, summarize_meal

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

_CONTENT_TYPE_TO_FORMAT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/heic": "heic",
    "image/heif": "heic",
}


def _detect_image_format(image: UploadFile) -> str:
    """Prefer the browser-reported MIME type over the filename extension —
    the filename can arrive mangled when a client sends it in a non-UTF-8
    encoding (e.g. a non-ASCII filename via curl on Windows), which silently
    strips the extension and breaks OCR with an empty format string.
    """
    if image.content_type in _CONTENT_TYPE_TO_FORMAT:
        return _CONTENT_TYPE_TO_FORMAT[image.content_type]
    if image.filename and "." in image.filename:
        ext = image.filename.rsplit(".", 1)[-1].lower()
        if ext:
            return ext
    return "jpg"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_receipt(image: UploadFile = File(...)) -> AnalyzeResponse:
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="empty image")

    image_format = _detect_image_format(image)
    print(f"[DEBUG] content_type={image.content_type!r} filename={ascii(image.filename)} format={image_format!r}")
    ocr_text = await ocr_client.run_ocr(image_bytes, image_format=image_format)
    if not ocr_text:
        raise HTTPException(status_code=422, detail="OCR에서 텍스트를 인식하지 못했습니다")

    food_items = await parser.extract_food_items(ocr_text)
    if not food_items:
        return AnalyzeResponse(items=[], total_calories_kcal=0, raw_ocr_text=ocr_text)

    nutrition_items = await build_nutrition_items(food_items)
    total = sum(i.calories_kcal or 0 for i in nutrition_items)

    return AnalyzeResponse(
        items=nutrition_items,
        total_calories_kcal=total,
        raw_ocr_text=ocr_text,
    )


@router.post("/comment", response_model=CommentResponse)
async def generate_comment(body: CommentRequest) -> CommentResponse:
    comment = await summarize_meal(body.items)
    return CommentResponse(comment=comment)
