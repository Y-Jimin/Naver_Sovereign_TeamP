import { useMemo, useRef, useState } from "react";
import { UploadReceipt } from "./components/UploadReceipt";
import { MealCard } from "./components/MealCard";
import { ProfileForm } from "./components/ProfileForm";
import { DailySummary } from "./components/DailySummary";
import { analyzeReceipt, fetchMealComment, NutritionItem } from "./api/client";
import { Profile, getDailyTarget, sumNutrients } from "./nutrition";

interface Meal {
  id: number;
  items: NutritionItem[];
  comment: string | null;
  commentLoading: boolean;
  rawOcrText: string;
}

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(0);

  const consumed = useMemo(() => sumNutrients(meals.flatMap((m) => m.items)), [meals]);

  async function handleSelect(file: File) {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeReceipt(file);
      const mealId = nextId.current++;
      setMeals((prev) => [
        ...prev,
        { id: mealId, items: res.items, comment: null, commentLoading: res.items.length > 0, rawOcrText: res.raw_ocr_text },
      ]);

      if (res.items.length > 0) {
        fetchMealComment(res.items)
          .then((comment) => {
            setMeals((prev) => prev.map((m) => (m.id === mealId ? { ...m, comment } : m)));
          })
          .catch(() => {
            /* comment is a nice-to-have; silently skip on failure */
          })
          .finally(() => {
            setMeals((prev) => prev.map((m) => (m.id === mealId ? { ...m, commentLoading: false } : m)));
          });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  }

  function handleRemoveItem(mealId: number, itemIndex: number) {
    setMeals((prev) =>
      prev.map((m) => (m.id === mealId ? { ...m, items: m.items.filter((_, i) => i !== itemIndex) } : m))
    );
  }

  if (!profile) {
    return (
      <main className="app">
        <h1>영수증 영양성분 분석</h1>
        <ProfileForm onSubmit={setProfile} />
      </main>
    );
  }

  const target = getDailyTarget(profile);

  return (
    <main className="app">
      <h1>영수증 영양성분 분석</h1>
      <DailySummary target={target} consumed={consumed} />

      {meals.map((meal, i) => (
        <MealCard
          key={meal.id}
          mealNumber={i + 1}
          items={meal.items}
          comment={meal.comment}
          commentLoading={meal.commentLoading}
          rawOcrText={meal.rawOcrText}
          onRemoveItem={(itemIndex) => handleRemoveItem(meal.id, itemIndex)}
        />
      ))}

      {error && <p className="error">{error}</p>}
      <UploadReceipt onSelect={handleSelect} disabled={loading} className="add-meal-btn" label="+ 새 끼니 추가" />
    </main>
  );
}
