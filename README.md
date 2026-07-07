# 영수증 영양성분 분석 서비스

영수증 사진을 CLOVA OCR로 읽고, 음식 영양성분 RAG 검색 + HyperCLOVA X로 품목별 칼로리/영양성분을
분석해 보여주는 서비스. 유저 계정/DB 없음 — 음식 영양성분 데이터만 RAG 소스로 저장.

## 구조

```
BE/   FastAPI 서버 (OCR 연동, RAG 검색, HyperCLOVA X 연동)
FE/   React + Vite + TS 프론트엔드
```

## 동작 흐름

1. FE에서 영수증 이미지 업로드 → `POST /api/receipts/analyze`
2. BE: CLOVA OCR로 텍스트 추출
3. BE: HyperCLOVA X로 OCR 텍스트에서 음식/음료 품목명만 추출 (`app/services/parser.py`)
4. BE: 품목명을 임베딩해 로컬 음식 영양성분 벡터 인덱스에서 최유사 항목 검색 (`app/services/rag_store.py`)
5. BE: 검색된 영양정보로 응답 구성 + HyperCLOVA X로 한 줄 코멘트 생성 (`app/services/nutrition_analyzer.py`)
6. FE: 품목별 표 + 총 칼로리 + 코멘트 표시

## 실행

### BE

```bash
cd BE
pip install -r requirements.txt
cp .env.example .env   # CLOVA OCR/Studio 키, invoke URL 채우기
python -m data.scripts.build_index --csv data/food_nutrition.sample.csv --out data/food_index.pkl
uvicorn app.main:app --reload --port 8000
```

데이터/인덱스 준비는 `BE/data/README.md` 참고.

### FE

```bash
cd FE
npm install
cp .env.example .env   # VITE_API_BASE_URL 확인
npm run dev
```

## 배포 (NCP 서버)

로컬과 동일하지만 두 가지가 다릅니다: **외부에서 접속 가능하도록 바인딩**, **FE/BE가 서로를 공인 IP로 찾을 수 있도록 설정**.

```bash
# BE — --host 0.0.0.0 필수 (기본값은 서버 자기 자신만 허용)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# FE — vite.config.ts에 host: true 반영해둬서 npm run dev만 하면 0.0.0.0으로 바인딩됨
npm run dev
```

- ACG(NCP 방화벽)에서 5173, 8000 인바운드 포트를 열어야 함 (이미 완료).
- `BE/.env`의 `CORS_ORIGINS`에 FE가 실제로 열리는 주소(서버 공인 IP:5173)를 추가해야 함 — 안 하면 브라우저가 API 호출을 CORS로 차단함.
- `FE/.env`의 `VITE_API_BASE_URL`을 서버 공인 IP:8000으로 설정해야 함 — `localhost`로 두면 브라우저(사용자 PC) 자신을 가리키게 돼서 API 호출이 실패함.
- 둘 다 `.env.example`에 예시 값과 함께 주석으로 표시해뒀습니다.

## 남은 TODO (실제 연동 전 확인 필요)

- `CLOVA_OCR_INVOKE_URL`, `CLOVA_STUDIO_CHAT_URL`, `CLOVA_STUDIO_EMBEDDING_URL`은 NCP/CLOVA Studio
  콘솔에서 발급받은 실제 값으로 교체해야 합니다. 계정/도메인에 따라 요청·응답 필드명이 콘솔 문서와
  다를 수 있으니 `app/services/ocr_client.py`, `llm_client.py`, `embedding_client.py`의 payload를
  실제 API 응답과 대조해 조정하세요.
- CLOVA OCR에 Receipt 전용 도메인이 있다면 `ocr_client._extract_text`를 구조화된 필드(상품명/가격)를
  바로 읽도록 바꾸면 파싱 단계(`parser.py`)를 단순화할 수 있습니다.
- 전체 식약처 데이터로 `build_index.py`를 재실행해 `food_index.pkl`을 교체하세요.
