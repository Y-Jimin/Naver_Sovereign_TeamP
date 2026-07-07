import { NutritionItem } from "./api/client";

export type Gender = "male" | "female";

export interface Profile {
  age: number;
  gender: Gender;
}

export interface NutrientTotals {
  calories: number;
  carbs: number;
  protein: number;
  fat: number;
  sodium: number;
}

export const DEFAULT_GRAMS = 100;

export interface MealItem extends NutritionItem {
  grams: number;
}

// 2020 한국인 영양소 섭취기준(KDRIs) 에너지 필요추정량을 연령대별로 단순화한 표.
const CALORIE_TABLE: { maxAge: number; male: number; female: number }[] = [
  { maxAge: 2, male: 1000, female: 1000 },
  { maxAge: 5, male: 1400, female: 1400 },
  { maxAge: 8, male: 1600, female: 1600 },
  { maxAge: 11, male: 1900, female: 1700 },
  { maxAge: 14, male: 2500, female: 2000 },
  { maxAge: 18, male: 2700, female: 2000 },
  { maxAge: 29, male: 2600, female: 2000 },
  { maxAge: 49, male: 2500, female: 1900 },
  { maxAge: 64, male: 2200, female: 1700 },
  { maxAge: 74, male: 2000, female: 1600 },
  { maxAge: Infinity, male: 1900, female: 1500 },
];

// 나트륨 목표섭취량(만성질환위험감소섭취량)은 성인 공통 2,000mg으로 고정.
const SODIUM_TARGET_MG = 2000;

// 탄:단:지 = 60:15:25 (AMDR 중간값 근사), kcal/g: 탄4 단4 지9.
const CARB_RATIO = 0.6;
const PROTEIN_RATIO = 0.15;
const FAT_RATIO = 0.25;

export function getDailyTarget({ age, gender }: Profile): NutrientTotals {
  const bracket = CALORIE_TABLE.find((b) => age <= b.maxAge) ?? CALORIE_TABLE[CALORIE_TABLE.length - 1];
  const calories = gender === "male" ? bracket.male : bracket.female;

  return {
    calories,
    carbs: Math.round((calories * CARB_RATIO) / 4),
    protein: Math.round((calories * PROTEIN_RATIO) / 4),
    fat: Math.round((calories * FAT_RATIO) / 9),
    sodium: SODIUM_TARGET_MG,
  };
}

// DB 영양값은 전부 100g(또는 100ml) 기준이라, 실제 섭취량(g)에 비례해 스케일링한다.
export function scaledNutrients(item: NutritionItem, grams: number): NutrientTotals {
  const factor = grams / 100;
  return {
    calories: (item.calories_kcal ?? 0) * factor,
    carbs: (item.carbs_g ?? 0) * factor,
    protein: (item.protein_g ?? 0) * factor,
    fat: (item.fat_g ?? 0) * factor,
    sodium: (item.sodium_mg ?? 0) * factor,
  };
}

export function sumMealItems(items: MealItem[]): NutrientTotals {
  return items.reduce(
    (acc, item) => {
      const s = scaledNutrients(item, item.grams);
      return {
        calories: acc.calories + s.calories,
        carbs: acc.carbs + s.carbs,
        protein: acc.protein + s.protein,
        fat: acc.fat + s.fat,
        sodium: acc.sodium + s.sodium,
      };
    },
    { calories: 0, carbs: 0, protein: 0, fat: 0, sodium: 0 }
  );
}
