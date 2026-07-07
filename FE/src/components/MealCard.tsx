import { MealItem, scaledNutrients } from "../nutrition";

const CONFIDENCE_LABEL: Record<string, string> = {
  high: "일치",
  medium: "유사 추정",
  low: "추정 불확실",
  label: "직접 입력값",
};

interface Props {
  mealNumber: number;
  items: MealItem[];
  comment: string | null;
  commentLoading: boolean;
  rawOcrText: string;
  onRemoveItem: (index: number) => void;
  onGramsChange: (index: number, grams: number) => void;
  onNameChange: (index: number, name: string) => void;
  onRequestComment: () => void;
}

function fmt(n: number): string {
  return Math.round(n * 10) / 10 + "";
}

export function MealCard({
  mealNumber,
  items,
  comment,
  commentLoading,
  rawOcrText,
  onRemoveItem,
  onGramsChange,
  onNameChange,
  onRequestComment,
}: Props) {
  const subtotal = items.reduce((sum, item) => sum + scaledNutrients(item, item.grams).calories, 0);

  return (
    <div className="meal-card">
      <div className="meal-card-header">
        <h3>끼니 {mealNumber}</h3>
        <span>{Math.round(subtotal)} kcal</span>
      </div>

      {items.length === 0 ? (
        <p className="muted">모든 품목이 삭제되었습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>영수증 품목</th>
              <th>음식 이름</th>
              <th>섭취량(g)</th>
              <th>kcal</th>
              <th>탄(g)</th>
              <th>단(g)</th>
              <th>지(g)</th>
              <th>나트륨(mg)</th>
              <th>매칭 정확도</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => {
              const scaled = scaledNutrients(item, item.grams);
              return (
                <tr key={i} className={`confidence-${item.confidence}`}>
                  <td>{item.source === "label" ? "영양성분표" : item.receipt_name}</td>
                  <td>
                    {item.source === "label" ? (
                      <input
                        className="name-input"
                        type="text"
                        placeholder="음식 이름 입력"
                        value={item.matched_food ?? ""}
                        onChange={(e) => onNameChange(i, e.target.value)}
                      />
                    ) : (
                      item.matched_food ?? "-"
                    )}
                  </td>
                  <td>
                    <input
                      className="grams-input"
                      type="number"
                      min={0}
                      value={item.grams}
                      onChange={(e) => onGramsChange(i, Number(e.target.value))}
                    />
                  </td>
                  <td>{item.calories_kcal != null ? fmt(scaled.calories) : "-"}</td>
                  <td>{item.carbs_g != null ? fmt(scaled.carbs) : "-"}</td>
                  <td>{item.protein_g != null ? fmt(scaled.protein) : "-"}</td>
                  <td>{item.fat_g != null ? fmt(scaled.fat) : "-"}</td>
                  <td>{item.sodium_mg != null ? fmt(scaled.sodium) : "-"}</td>
                  <td title={item.note ?? undefined}>
                    {CONFIDENCE_LABEL[item.confidence]}
                    {item.similarity != null && ` (${Math.round(item.similarity * 100)}%)`}
                  </td>
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
              );
            })}
          </tbody>
        </table>
      )}

      {items.length > 0 && (
        <p className="muted grams-hint">
          매칭된 영양성분은 100g(또는 100ml) 기준값입니다 — 실제 먹은 양(g)을 입력하면 그에 맞게 계산됩니다.
        </p>
      )}

      {commentLoading && <p className="comment comment-loading">코멘트 생성 중...</p>}
      {!commentLoading && comment && <p className="comment">{comment}</p>}
      {!commentLoading && !comment && items.length > 0 && (
        <button className="comment-btn" onClick={onRequestComment}>
          먹은 항목으로 영양 메시지 받기
        </button>
      )}

      <details>
        <summary>OCR 원문 보기</summary>
        <pre>{rawOcrText}</pre>
      </details>
    </div>
  );
}
