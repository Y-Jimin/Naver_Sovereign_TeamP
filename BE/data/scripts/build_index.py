"""Build the local RAG index from one or more food nutrition CSVs.

Usage (run from BE/ directory so `app` is importable):
    python -m data.scripts.build_index --csv data/food_nutrition.csv --out data/food_index.pkl

Pass --csv multiple times to merge several sources into one index, e.g. the
raw-ingredient, processed-food, and prepared-dish variants of 식약처's
전국통합식품영양성분정보 dataset:
    python -m data.scripts.build_index \\
        --csv data/food_raw_ingredients.csv \\
        --csv data/food_processed.csv \\
        --csv data/food_dishes.csv \\
        --out data/food_index.pkl

Expected CSV columns (English or the raw 식약처 Korean names are both accepted):
    name / 식품명
    calories_kcal / 에너지(kcal)
    carbs_g / 탄수화물(g)
    protein_g / 단백질(g)
    fat_g / 지방(g)
    sodium_mg / 나트륨(mg)

For large files (tens of thousands of rows) this embeds concurrently and
writes a checkpoint every --checkpoint-every rows. If the process is killed
or an API call keeps failing, re-run the same command — it loads the
checkpoint at --out and skips names it already embedded.
"""

import argparse
import asyncio
import csv
import pickle
import sys
import time
from pathlib import Path

import httpx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # allow `app.*` imports

from app.services.embedding_client import embed_text  # noqa: E402
from app.services.rag_store import FoodEntry  # noqa: E402

COLUMN_ALIASES = {
    "name": ["name", "식품명"],
    "calories_kcal": ["calories_kcal", "에너지(kcal)", "에너지"],
    "carbs_g": ["carbs_g", "탄수화물(g)", "탄수화물"],
    "protein_g": ["protein_g", "단백질(g)", "단백질"],
    "fat_g": ["fat_g", "지방(g)", "지방"],
    "sodium_mg": ["sodium_mg", "나트륨(mg)", "나트륨"],
}

MAX_RETRIES = 5


class RateLimiter:
    """Paces requests to a fixed rate regardless of concurrency, so we stay
    under the account's requests/sec quota instead of bursting into 429s and
    burning time on retry backoff.
    """

    def __init__(self, rate_per_sec: float) -> None:
        self._interval = 1.0 / rate_per_sec
        self._lock = asyncio.Lock()
        self._next_slot = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            slot = max(now, self._next_slot)
            self._next_slot = slot + self._interval
        delay = slot - now
        if delay > 0:
            await asyncio.sleep(delay)


def _resolve_columns(header: list[str]) -> dict[str, str]:
    resolved = {}
    for field, aliases in COLUMN_ALIASES.items():
        match = next((a for a in aliases if a in header), None)
        if match is None:
            raise ValueError(f"CSV is missing a column for '{field}' (tried {aliases})")
        resolved[field] = match
    return resolved


def _to_float(value: str) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _load_rows(csv_paths: list[str]) -> list[FoodEntry]:
    entries: list[FoodEntry] = []
    seen_names: set[str] = set()
    for csv_path in csv_paths:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            columns = _resolve_columns(reader.fieldnames or [])
            rows = list(reader)

        added = 0
        for row in rows:
            name = row[columns["name"]].strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            added += 1
            entries.append(
                FoodEntry(
                    name=name,
                    calories_kcal=_to_float(row[columns["calories_kcal"]]),
                    carbs_g=_to_float(row[columns["carbs_g"]]),
                    protein_g=_to_float(row[columns["protein_g"]]),
                    fat_g=_to_float(row[columns["fat_g"]]),
                    sodium_mg=_to_float(row[columns["sodium_mg"]]),
                )
            )
        print(f"{csv_path}: {len(rows)} rows -> {added} new unique foods")
    return entries


def _load_checkpoint(out_path: str) -> tuple[list[FoodEntry], list[np.ndarray]]:
    if not Path(out_path).exists():
        return [], []
    with open(out_path, "rb") as f:
        data = pickle.load(f)
    vectors = list(data["vectors"]) if len(data["entries"]) else []
    return data["entries"], vectors


def _save_checkpoint(out_path: str, entries: list[FoodEntry], vectors: list[np.ndarray]) -> None:
    tmp_path = f"{out_path}.tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump({"entries": entries, "vectors": np.stack(vectors)}, f)
    Path(tmp_path).replace(out_path)  # atomic on the same filesystem


async def _embed_with_retry(name: str, semaphore: asyncio.Semaphore, limiter: RateLimiter) -> np.ndarray:
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            await limiter.wait()
            try:
                vec = await embed_text(name)
                return vec / (np.linalg.norm(vec) + 1e-8)
            except httpx.HTTPStatusError as e:
                is_rate_limited = e.response.status_code in (429, 500, 502, 503)
                if not is_rate_limited or attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise RuntimeError("unreachable")


async def main(
    csv_paths: list[str], out_path: str, concurrency: int, rate: float, checkpoint_every: int, limit: int | None
) -> None:
    all_entries = _load_rows(csv_paths)
    if limit:
        all_entries = all_entries[:limit]

    done_entries, done_vectors = _load_checkpoint(out_path)
    done_names = {e.name for e in done_entries}
    todo = [e for e in all_entries if e.name not in done_names]

    print(f"total unique foods: {len(all_entries)} | already embedded: {len(done_entries)} | remaining: {len(todo)}")
    if not todo:
        print("nothing to do")
        return

    semaphore = asyncio.Semaphore(concurrency)
    limiter = RateLimiter(rate)
    entries = done_entries
    vectors = done_vectors
    start = time.monotonic()

    for batch_start in range(0, len(todo), checkpoint_every):
        batch = todo[batch_start : batch_start + checkpoint_every]
        results = await asyncio.gather(
            *(_embed_with_retry(e.name, semaphore, limiter) for e in batch), return_exceptions=True
        )
        for entry, result in zip(batch, results):
            if isinstance(result, Exception):
                print(f"[skip] '{entry.name}' failed after retries: {result}")
                continue
            entries.append(entry)
            vectors.append(result)

        _save_checkpoint(out_path, entries, vectors)
        elapsed = time.monotonic() - start
        done_count = len(entries) - len(done_entries)
        rate = done_count / elapsed if elapsed > 0 else 0
        print(
            f"checkpoint saved: {len(entries)}/{len(all_entries)} total "
            f"({rate:.1f} items/sec, {elapsed:.0f}s elapsed)"
        )

    print(f"done. wrote {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="append", default=None, help="repeatable; merges multiple CSVs")
    parser.add_argument("--out", default="data/food_index.pkl")
    parser.add_argument("--concurrency", type=int, default=3, help="max requests in flight at once")
    parser.add_argument(
        "--rate", type=float, default=0.8, help="max requests per second, paced regardless of concurrency"
    )
    parser.add_argument("--checkpoint-every", type=int, default=200, help="rows per checkpoint save")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N rows (for a dry run)")
    args = parser.parse_args()
    csv_paths = args.csv or ["data/food_nutrition.csv"]
    asyncio.run(main(csv_paths, args.out, args.concurrency, args.rate, args.checkpoint_every, args.limit))
