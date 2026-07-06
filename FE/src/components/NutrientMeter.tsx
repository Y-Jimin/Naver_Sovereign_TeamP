interface Props {
  label: string;
  unit: string;
  consumed: number;
  target: number;
}

export function NutrientMeter({ label, unit, consumed, target }: Props) {
  const ratio = target > 0 ? consumed / target : 0;
  const remaining = target - consumed;
  const state = ratio > 1 ? "critical" : ratio >= 0.9 ? "warning" : "normal";

  return (
    <div className="meter">
      <div className="meter-label">{label}</div>
      <div className="meter-value">
        {Math.round(consumed)} / {Math.round(target)} {unit}
      </div>
      <div className="meter-track">
        <div className={`meter-fill meter-fill-${state}`} style={{ width: `${Math.min(ratio, 1) * 100}%` }} />
      </div>
      <div className={`meter-remaining meter-remaining-${state}`}>
        {remaining >= 0 ? `남음 ${Math.round(remaining)}${unit}` : `⚠ 초과 ${Math.round(-remaining)}${unit}`}
      </div>
    </div>
  );
}
