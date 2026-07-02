interface ScoreBarProps {
  label: string;
  value: number;
}

export function ScoreBar({ label, value }: ScoreBarProps) {
  const normalizedValue = Math.max(0, Math.min(value * 10, 100));
  return (
    <div className="score-bar">
      <span>{label}</span>
      <div className="bar-track">
        <i style={{ width: `${normalizedValue}%` }} />
      </div>
      <strong>{formatScore(value)}</strong>
    </div>
  );
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}
