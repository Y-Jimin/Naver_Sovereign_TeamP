import { NutrientTotals } from "../nutrition";
import { NutrientMeter } from "./NutrientMeter";

interface Props {
  target: NutrientTotals;
  consumed: NutrientTotals;
}

export function DailySummary({ target, consumed }: Props) {
  return (
    <section className="daily-summary">
      <h2>오늘의 영양 현황</h2>
      <div className="meter-row">
        <NutrientMeter label="칼로리" unit="kcal" consumed={consumed.calories} target={target.calories} />
        <NutrientMeter label="탄수화물" unit="g" consumed={consumed.carbs} target={target.carbs} />
        <NutrientMeter label="단백질" unit="g" consumed={consumed.protein} target={target.protein} />
        <NutrientMeter label="지방" unit="g" consumed={consumed.fat} target={target.fat} />
        <NutrientMeter label="나트륨" unit="mg" consumed={consumed.sodium} target={target.sodium} />
      </div>
    </section>
  );
}
