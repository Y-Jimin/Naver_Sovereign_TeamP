from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import receipts
from app.services.rag_store import food_rag_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        food_rag_store.load()
    except FileNotFoundError:
        print(f"[warn] RAG index not found at {settings.rag_index_path} — run data/scripts/build_index.py first")
    yield


app = FastAPI(title="Receipt Nutrition Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
