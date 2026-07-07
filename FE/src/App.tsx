import { useMemo, useRef, useState } from "react";
import { UploadReceipt } from "./components/UploadReceipt";
import { MealCard } from "./components/MealCard";
import { ProfileForm } from "./components/ProfileForm";
import { DailySummary } from "./components/DailySummary";
import { analyzeReceipt, fetchMealComment, NutritionItem } from "./api/client";
import { Profile, getDailyTarget, sumMealItems, scaledNutrients, MealItem, DEFAULT_GRAMS } from "./nutrition";

interface Meal {
  id: number;
  items: MealItem[];
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

  const consumed = useMemo(() => sumMealItems(meals.flatMap((m) => m.items)), [meals]);

  async function handleSelect(file: File) {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeReceipt(file);
      const mealId = nextId.current++;
      const items: MealItem[] = res.items.map((item) => ({ ...item, grams: DEFAULT_GRAMS }));
      setMeals((prev) => [
        ...prev,
        { id: mealId, items, comment: null, commentLoading: false, rawOcrText: res.raw_ocr_text },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  }

  function handleRemoveItem(mealId: number, itemIndex: number) {
    setMeals((prev) =>
      prev.map((m) =>
        m.id === mealId ? { ...m, items: m.items.filter((_, i) => i !== itemIndex), comment: null } : m
      )
    );
  }

  function handleGramsChange(mealId: number, itemIndex: number, grams: number) {
    setMeals((prev) =>
      prev.map((m) =>
        m.id === mealId
          ? { ...m, items: m.items.map((it, i) => (i === itemIndex ? { ...it, grams } : it)), comment: null }
          : m
      )
    );
  }

  function handleNameChange(mealId: number, itemIndex: number, name: string) {
    setMeals((prev) =>
      prev.map((m) =>
        m.id === mealId
          ? { ...m, items: m.items.map((it, i) => (i === itemIndex ? { ...it, matched_food: name } : it)) }
          : m
      )
    );
  }

  function handleRequestComment(mealId: number) {
    const meal = meals.find((m) => m.id === mealId);
    if (!meal || meal.items.length === 0) return;

    // 코멘트는 100g 기준값이 아니라 실제 섭취량(g)으로 스케일된 값을 근거로 만들어야 함.
    const scaledItems: NutritionItem[] = meal.items.map((item) => {
      const s = scaledNutrients(item, item.grams);
      return {
        ...item,
        calories_kcal: s.calories,
        carbs_g: s.carbs,
        protein_g: s.protein,
        fat_g: s.fat,
        sodium_mg: s.sodium,
      };
    });

    setMeals((prev) => prev.map((m) => (m.id === mealId ? { ...m, commentLoading: true } : m)));
    fetchMealComment(scaledItems)
      .then((comment) => {
        setMeals((prev) => prev.map((m) => (m.id === mealId ? { ...m, comment } : m)));
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "코멘트 생성에 실패했습니다");
      })
      .finally(() => {
        setMeals((prev) => prev.map((m) => (m.id === mealId ? { ...m, commentLoading: false } : m)));
      });
  }

  if (!profile) {
    return (
      <main className="app">
        <h1>스냅밀[Snap Meal]</h1>
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
          onGramsChange={(itemIndex, grams) => handleGramsChange(meal.id, itemIndex, grams)}
          onNameChange={(itemIndex, name) => handleNameChange(meal.id, itemIndex, name)}
          onRequestComment={() => handleRequestComment(meal.id)}
        />
      ))}

      {error && <p className="error">{error}</p>}
      <UploadReceipt onSelect={handleSelect} disabled={loading} className="add-meal-btn" label="+ 새 끼니 추가" />
    </main>
  );
}
