"""Fetch a full 공공데이터포털(data.go.kr) 표준데이터셋 Open API dataset and save it
as a CSV with the same column names build_index.py expects.

The grid/file download on data.go.kr is capped at 50,000 rows; the Open API
has no such cap (subject to your daily traffic quota), so this is how you get
everything (e.g. the 음식/외식 메뉴 dataset).

Every data.go.kr Open API needs two things you copy from the dataset's
"Open API" tab *after* 활용신청 is approved (보통 즉시 자동승인):
    1. the request URL (--url)
    2. your service key (--service-key)

Because response field names are NOT guaranteed to match the Korean grid
headers (식품명, 에너지(kcal) ...), first run with --probe to inspect the
raw fields, then re-run with --field-map pointing the real fields at our
standard columns.

Usage:
    # 1) inspect what fields the API actually returns
    python -m data.scripts.fetch_openapi --url "<요청 URL>" --service-key "<키>" --probe

    # 2) write a field map JSON, e.g. data/scripts/field_map_raw.json:
    #    {"FOOD_NM": "식품명", "AMT_NUM1": "에너지(kcal)", "AMT_NUM6": "탄수화물(g)",
    #     "AMT_NUM3": "단백질(g)", "AMT_NUM4": "지방(g)", "AMT_NUM13": "나트륨(mg)"}

    # 3) fetch everything
    python -m data.scripts.fetch_openapi --url "<요청 URL>" --service-key "<키>" \\
        --field-map data/scripts/field_map_raw.json --out data/food_raw.csv
"""

import argparse
import asyncio
import csv
import json
from urllib.parse import quote

import httpx

STANDARD_COLUMNS = ["식품명", "에너지(kcal)", "탄수화물(g)", "단백질(g)", "지방(g)", "나트륨(mg)"]


async def _fetch_page(
    client: httpx.AsyncClient,
    url: str,
    service_key: str,
    page_no: int,
    num_of_rows: int,
    raw_key: bool,
    extra_params: dict[str, str] | None = None,
) -> dict:
    extra_params = extra_params or {}
    if raw_key:
        # service key already URL-encoded (the "Encoding" key from data.go.kr) —
        # splice it in ourselves so httpx doesn't double-encode it.
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}serviceKey={service_key}&pageNo={page_no}&numOfRows={num_of_rows}&type=json"
        for k, v in extra_params.items():
            full_url += f"&{k}={quote(str(v))}"
        resp = await client.get(full_url, timeout=60)
    else:
        params = {"serviceKey": service_key, "pageNo": page_no, "numOfRows": num_of_rows, "type": "json"}
        params.update(extra_params)
        resp = await client.get(url, params=params, timeout=60)

    resp.raise_for_status()
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"응답이 JSON이 아닙니다 (앞 300자): {resp.text[:300]!r}\n"
            "→ type=xml만 지원하는 API일 수도 있고, URL/서비스키가 틀렸을 수도 있습니다."
        ) from e


def _extract_items(payload: dict) -> tuple[list[dict], int]:
    body = payload.get("response", {}).get("body", payload.get("body", payload))
    items = body.get("items", [])
    if isinstance(items, dict):  # some APIs wrap a single item without a list
        items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
    total_count = int(body.get("totalCount", len(items)))
    return items, total_count


async def probe(url: str, service_key: str, raw_key: bool, extra_params: dict[str, str] | None = None) -> None:
    async with httpx.AsyncClient() as client:
        payload = await _fetch_page(client, url, service_key, page_no=1, num_of_rows=5, raw_key=raw_key, extra_params=extra_params)
    items, total_count = _extract_items(payload)
    print(f"totalCount: {total_count}")
    print(f"sample item count: {len(items)}")
    if items:
        print("첫 항목의 필드들:")
        print(json.dumps(items[0], ensure_ascii=False, indent=2))
    else:
        print("items가 비어있습니다. 전체 응답:")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000])


async def fetch_all(
    url: str,
    service_key: str,
    out_path: str,
    field_map: dict[str, str] | None,
    page_size: int,
    raw_key: bool,
    extra_params: dict[str, str] | None = None,
) -> None:
    async with httpx.AsyncClient() as client:
        first = await _fetch_page(
            client, url, service_key, page_no=1, num_of_rows=page_size, raw_key=raw_key, extra_params=extra_params
        )
        items, total_count = _extract_items(first)
        all_items = list(items)
        print(f"totalCount: {total_count}")

        page_no = 2
        while len(all_items) < total_count:
            await asyncio.sleep(0.2)  # be polite to the API
            payload = await _fetch_page(client, url, service_key, page_no, page_size, raw_key, extra_params)
            items, _ = _extract_items(payload)
            if not items:
                print(f"[warn] page {page_no}에서 빈 응답, {len(all_items)}/{total_count}에서 중단")
                break
            all_items.extend(items)
            page_no += 1
            if page_no % 10 == 0 or len(all_items) >= total_count:
                print(f"fetched {len(all_items)}/{total_count}")

    columns = STANDARD_COLUMNS if field_map else sorted({k for item in all_items for k in item})
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for item in all_items:
            if field_map:
                row = [item.get(src, "") for src in _standard_to_source(field_map)]
            else:
                row = [item.get(c, "") for c in columns]
            writer.writerow(row)

    print(f"wrote {len(all_items)} rows to {out_path}")
    if not field_map:
        print(
            "필드맵 없이 원본 필드명으로 저장했습니다. build_index.py가 읽게 하려면 "
            "--field-map으로 표준 컬럼명에 매핑해서 다시 실행하거나, "
            "build_index.py의 COLUMN_ALIASES에 이 필드명을 추가하세요."
        )


def _standard_to_source(field_map: dict[str, str]) -> list[str]:
    """field_map is {source_field: standard_column}; invert to fetch in STANDARD_COLUMNS order."""
    inverted = {v: k for k, v in field_map.items()}
    missing = [c for c in STANDARD_COLUMNS if c not in inverted]
    if missing:
        raise ValueError(f"--field-map에 다음 표준 컬럼이 빠졌습니다: {missing}")
    return [inverted[c] for c in STANDARD_COLUMNS]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Open API 탭에서 복사한 요청 URL (serviceKey 앞부분까지)")
    parser.add_argument("--service-key", required=True)
    parser.add_argument(
        "--raw-key",
        action="store_true",
        help="서비스키가 이미 URL-인코딩된 값(Encoding 키)이면 사용. 기본은 Decoding 키를 가정.",
    )
    parser.add_argument("--probe", action="store_true", help="첫 페이지만 가져와서 필드명 확인 후 종료")
    parser.add_argument("--field-map", default=None, help="{원본필드: 표준컬럼명} JSON 파일 경로")
    parser.add_argument("--out", default="data/food_openapi.csv")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument(
        "--extra-param",
        action="append",
        default=None,
        metavar="KEY=VALUE",
        help="repeatable; extra query params for server-side filtering (e.g. --extra-param dataCd=R)",
    )
    args = parser.parse_args()
    extra = dict(p.split("=", 1) for p in args.extra_param) if args.extra_param else None

    if args.probe:
        asyncio.run(probe(args.url, args.service_key, args.raw_key, extra))
    else:
        fmap = None
        if args.field_map:
            with open(args.field_map, encoding="utf-8") as f:
                fmap = json.load(f)
        asyncio.run(fetch_all(args.url, args.service_key, args.out, fmap, args.page_size, args.raw_key, extra))
