interface Props {
  size?: number;
  className?: string;
}

export function Spinner({ size = 16, className }: Props) {
  return (
    <span
      className={`spinner ${className ?? ""}`}
      style={{ width: size, height: size }}
      role="status"
      aria-label="로딩 중"
    />
  );
}
