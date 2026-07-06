import { FormEvent, useState } from "react";
import { Gender, Profile } from "../nutrition";

interface Props {
  onSubmit: (profile: Profile) => void;
}

export function ProfileForm({ onSubmit }: Props) {
  const [age, setAge] = useState("");
  const [gender, setGender] = useState<Gender>("male");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parsedAge = Number(age);
    if (!parsedAge || parsedAge <= 0) return;
    onSubmit({ age: parsedAge, gender });
  }

  return (
    <form className="profile-form" onSubmit={handleSubmit}>
      <h2>내 정보 입력</h2>
      <p className="muted">나이와 성별로 하루 권장 칼로리/영양성분을 계산합니다.</p>
      <label>
        나이
        <input
          type="number"
          min={1}
          max={120}
          value={age}
          onChange={(e) => setAge(e.target.value)}
          required
        />
      </label>
      <label>
        성별
        <select value={gender} onChange={(e) => setGender(e.target.value as Gender)}>
          <option value="male">남성</option>
          <option value="female">여성</option>
        </select>
      </label>
      <button type="submit">시작하기</button>
    </form>
  );
}
