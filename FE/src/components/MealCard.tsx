import { NutritionItem } from "../api/client";

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "일치",
  medium: "유사 추정",
  low: "추정 불확실",
};

interface Props {
  mealNumber: number;
  items: NutritionItem[];
  comment: string | null;
  commentLoading: boolean;
  rawOcrText: string;
  onRemoveItem: (index: number) => void;
}

export function MealCard({ mealNumber, items, comment, commentLoading, rawOcrText, onRemoveItem }: Props) {
  const subtotal = items.reduce((sum, item) => sum + (item.calories_kcal ?? 0), 0);

  return (
    <div className="meal-card">
      <div className="meal-card-header">
        <h3>끼니 {mealNumber}</h3>
        <span>{Math.round(subtotal)} kcal</span>
      </div>

      {commentLoading && <p className="comment comment-loading">코멘트 생성 중...</p>}
      {!commentLoading && comment && <p className="comment">{comment}</p>}

      {items.length === 0 ? (
        <p className="muted">모든 품목이 삭제되었습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>영수증 품목</th>
              <th>매칭된 음식</th>
              <th>kcal</th>
              <th>탄(g)</th>
              <th>단(g)</th>
              <th>지(g)</th>
              <th>나트륨(mg)</th>
              <th>신뢰도</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={i} className={`confidence-${item.confidence}`}>
                <td>{item.receipt_name}</td>
                <td>{item.matched_food ?? "-"}</td>
                <td>{item.calories_kcal ?? "-"}</td>
                <td>{item.carbs_g ?? "-"}</td>
                <td>{item.protein_g ?? "-"}</td>
                <td>{item.fat_g ?? "-"}</td>
                <td>{item.sodium_mg ?? "-"}</td>
                <td title={item.note ?? undefined}>{CONFIDENCE_LABEL[item.confidence]}</td>
                <td>
                  <button
                    className="remove-item-btn"
                    title="이 품목 삭제 (내가 먹은 게 아님)"
                    onClick={() => onRemoveItem(i)}
                  >
                    −
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <details>
        <summary>OCR 원문 보기</summary>
        <pre>{rawOcrText}</pre>
      </details>
    </div>
  );
}
