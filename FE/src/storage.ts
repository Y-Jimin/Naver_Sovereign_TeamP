import { Profile } from "./nutrition";
import { MealItem } from "./nutrition";

export interface Meal {
  id: number;
  items: MealItem[];
  comment: string | null;
  commentLoading: boolean;
  rawOcrText: string;
}

const PROFILE_KEY = "snapmeal:profile";
const MEALS_KEY = "snapmeal:meals";

export function loadProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveProfile(profile: Profile): void {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch {
    // localStorage 사용 불가(사파리 프라이빗 모드 등) — 저장 실패해도 앱은 계속 동작
  }
}

export function loadMeals(): Meal[] {
  try {
    const raw = localStorage.getItem(MEALS_KEY);
    if (!raw) return [];
    const parsed: Meal[] = JSON.parse(raw);
    // 새로고침 전에 끊긴 요청 상태(로딩중)는 복원하지 않음 — 그대로 두면 영원히 로딩중으로 보임
    return parsed.map((m) => ({ ...m, commentLoading: false }));
  } catch {
    return [];
  }
}

export function saveMeals(meals: Meal[]): void {
  try {
    localStorage.setItem(MEALS_KEY, JSON.stringify(meals));
  } catch {
    // 위와 동일한 이유로 실패는 무시
  }
}
