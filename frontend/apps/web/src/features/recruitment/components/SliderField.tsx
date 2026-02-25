"use client";

/** Labelled range slider (0–1, step 0.05) */
export function SliderField({
  label,
  value,
  onChange,
  leftLabel,
  rightLabel,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  leftLabel: string;
  rightLabel: string;
}) {
  const pct = Math.round(value * 100);
  const color = pct >= 66 ? "#22C55E" : pct >= 33 ? "#F59E0B" : "#EF4444";
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between items-center">
        <span className="text-xs text-muted">{label}</span>
        <span className="text-xs font-semibold" style={{ color }}>{pct}</span>
      </div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1 rounded-full appearance-none cursor-pointer"
        style={{ accentColor: color }}
      />
      <div className="flex justify-between text-xs text-muted/60">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
}
