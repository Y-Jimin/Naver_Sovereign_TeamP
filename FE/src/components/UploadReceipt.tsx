import { ChangeEvent, useRef } from "react";

interface Props {
  onSelect: (file: File) => void;
  disabled: boolean;
  className?: string;
  label?: string;
}

export function UploadReceipt({ onSelect, disabled, className, label }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onSelect(file);
    e.target.value = "";
  }

  return (
    <div className={`upload-box ${className ?? ""}`}>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleChange}
        disabled={disabled}
        hidden
      />
      <button onClick={() => inputRef.current?.click()} disabled={disabled}>
        {disabled ? "분석 중..." : label ?? "영수증 촬영/업로드"}
      </button>
    </div>
  );
}
