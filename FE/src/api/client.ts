export interface NutritionItem {
  receipt_name: string;
  matched_food: string | null;
  // 매칭된 음식의 100g(또는 100ml) 기준값. 실제 섭취량(g)에 맞춰 스케일링해서 써야 함.
  calories_kcal: number | null;
  carbs_g: number | null;
  protein_g: number | null;
  fat_g: number | null;
  sodium_mg: number | null;
  confidence: "high" | "medium" | "low" | "label";
  similarity: number | null;
  note: string | null;
  source: "receipt" | "label";
}

export interface AnalyzeResponse {
  items: NutritionItem[];
  total_calories_kcal: number;
  raw_ocr_text: string;
  comment: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeReceipt(image: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("image", image);

  const res = await fetch(`${API_BASE_URL}/api/receipts/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `분석 요청 실패 (${res.status})`);
  }

  return res.json();
}

export async function fetchMealComment(items: NutritionItem[]): Promise<string | null> {
  const res = await fetch(`${API_BASE_URL}/api/receipts/comment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `코멘트 생성 실패 (${res.status})`);
  }

  const data: { comment: string | null } = await res.json();
  return data.comment;
}
