# 음식 영양성분 데이터 (RAG 소스)

## 1. 전체 데이터 확보

"전국통합식품영양성분정보표준데이터"는 사실 **3개로 분리된 자매 데이터셋**입니다. 영수증에는 마트
원재료(양파/무/우유 등)와 음식점 메뉴, 편의점 가공식품이 섞여 나오므로 **셋 다 받아서 합치는 걸 권장**합니다.

- [원재료성식품](https://www.data.go.kr/data/15100065/standard.do) → `data/food_raw.csv` — 낱개 농산물/축산물/수산물 (양파, 무, 우유, 브로콜리 등). 마트 영수증엔 이게 꼭 있어야 매칭됩니다.
- [가공식품](https://www.data.go.kr/data/15100066/standard.do) → `data/food_processed.csv` — 바코드 있는 브랜드 포장 제품 (편의점/마트).
- [음식](https://www.data.go.kr/data/15100070/standard.do) → `data/food_dishes.csv` — 된장찌개/비빔밥 등 조리된 음식점 메뉴.

공공데이터포털의 그리드형 다운로드는 **5만 건 제한**이 있습니다. 그 이상이 필요하면(특히 음식/외식
메뉴 데이터셋) Open API로 받으세요.

### Open API로 5만 건 넘게 받기

1. 데이터셋 페이지(예: [음식](https://www.data.go.kr/data/15100070/openapi.do))에서 "Open API" 탭 →
   활용신청 (보통 즉시 자동승인) → 마이페이지에서 발급된 서비스키 확인.
2. 같은 "Open API" 탭에 있는 **요청 URL**을 그대로 복사해서 `--url`에 넣고, 필드명부터 확인:
   ```bash
   python -m data.scripts.fetch_openapi --url "<복사한 요청 URL>" --service-key "<발급받은 키>" --probe
   ```
   `AMT_NUM1`처럼 그리드 CSV 헤더(`에너지(kcal)`)와 다른 필드명이 나올 수 있습니다. 출력된 필드명을 보고
   `data/scripts/field_map.json` 같은 파일을 만들어 표준 컬럼에 매핑하세요:
   ```json
   { "FOOD_NM": "식품명", "AMT_NUM1": "에너지(kcal)", "AMT_NUM6": "탄수화물(g)",
     "AMT_NUM3": "단백질(g)", "AMT_NUM4": "지방(g)", "AMT_NUM13": "나트륨(mg)" }
   ```
   (실제 필드명은 `--probe` 출력을 보고 채우세요 — 위 값은 예시입니다.)
3. 전체 수집:
   ```bash
   python -m data.scripts.fetch_openapi --url "<요청 URL>" --service-key "<키>" \
     --field-map data/scripts/field_map.json --out data/food_dishes.csv
   ```
   자동으로 페이지네이션하며 `totalCount`까지 다 받습니다.
4. 서비스키 관련 주의: 마이페이지에 키가 **Encoding(인코딩)**, **Decoding(디코딩)** 두 종류로 나옵니다.
   기본값은 Decoding 키를 넣는 걸 가정합니다. Encoding 키(이미 `%XX`가 포함된 값)를 쓴다면
   `--raw-key` 플래그를 추가하세요 — 안 그러면 이중 인코딩되어 인증이 실패합니다.
5. 일일 호출 한도가 있을 수 있습니다(마이페이지 > 활용신청 현황에서 확인). 429/한도 초과 에러가 나면
   시간을 두고 재시도하세요.

컬럼명이 아래 중 하나와 일치해야 합니다 (원본 그대로 써도 되고,
`build_index.py`의 `COLUMN_ALIASES`에 별칭을 추가해도 됩니다). 3개 데이터셋 모두 같은 표준 스키마라
컬럼명은 동일합니다:

> **인코딩 주의**: 이 공공데이터 CSV는 UTF-8이 아니라 CP949(EUC-KR)로 내려오는 경우가 많습니다.
> 열었을 때 한글이 깨지면 CP949로 읽어서 UTF-8로 재저장하세요 (PowerShell 예시):
> ```powershell
> $content = [System.IO.File]::ReadAllText("원본파일.csv", [System.Text.Encoding]::GetEncoding(949))
> [System.IO.File]::WriteAllText("data/food_nutrition.csv", $content, [System.Text.UTF8Encoding]::new($false))
> ```

| 필드 | 허용되는 컬럼명 |
|---|---|
| 이름 | `name`, `식품명` |
| 칼로리 | `calories_kcal`, `에너지(kcal)` |
| 탄수화물 | `carbs_g`, `탄수화물(g)` |
| 단백질 | `protein_g`, `단백질(g)` |
| 지방 | `fat_g`, `지방(g)` |
| 나트륨 | `sodium_mg`, `나트륨(mg)` |

## 2. 인덱스 빌드 (CLOVA Studio 키 필요)

`food_nutrition.sample.csv`는 로컬 동작 확인용 10개 샘플입니다. 실제 서비스에는 1번에서 받은 데이터를
사용하세요. `--csv`를 여러 번 넘기면 자동으로 합쳐서 하나의 인덱스로 임베딩합니다.

```bash
cd BE
pip install -r requirements.txt
cp .env.example .env  # 값 채우기

# 1) 먼저 소규모로 파이프라인 확인
python -m data.scripts.build_index --csv data/food_nutrition.sample.csv --out data/food_index.pkl

# 2) 실제 데이터 (원재료 + 가공식품 + 음식 셋을 합쳐서 하나의 인덱스로)
python -m data.scripts.build_index \
  --csv data/food_raw.csv \
  --csv data/food_processed.csv \
  --csv data/food_dishes.csv \
  --out data/food_index.pkl --concurrency 5
```

- 완전히 동일한 식품명은 파일 내부·파일 간 모두 자동으로 중복 제거 후 1번만 임베딩합니다.
- `--concurrency`로 동시 요청 수를 조절하세요. CLOVA Studio 요청 제한(TPS/RPM)에 맞춰 너무 높이지 않도록 주의.
- `--checkpoint-every`(기본 200) 마다 `food_index.pkl`에 중간 저장합니다. 중간에 죽거나 Ctrl+C로 멈춰도
  **같은 명령을 다시 실행하면 이미 임베딩된 항목은 건너뛰고 이어서** 진행합니다.
- `--limit N`으로 처음 N개만 처리하는 드라이런이 가능합니다.
- 데이터가 바뀌면(신규/수정) 이 스크립트를 다시 실행해 `food_index.pkl`을 갱신해야 합니다.
