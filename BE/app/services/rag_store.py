import pickle
from dataclasses import dataclass

import numpy as np

from app.config import settings
from app.services.embedding_client import embed_text


@dataclass
class FoodEntry:
    name: str
    calories_kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float
    sodium_mg: float


class FoodRagStore:
    def __init__(self) -> None:
        self.entries: list[FoodEntry] = []
        self.vectors: np.ndarray | None = None  # shape (N, D), L2-normalized

    def load(self, path: str = settings.rag_index_path) -> None:
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.entries = data["entries"]
        self.vectors = data["vectors"]

    async def search(self, query: str, top_k: int = 3) -> list[tuple[FoodEntry, float]]:
        if self.vectors is None or len(self.entries) == 0:
            return []
        query_vec = await embed_text(query)
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        scores = self.vectors @ query_vec
        top_idx = np.argsort(-scores)[:top_k]
        return [(self.entries[i], float(scores[i])) for i in top_idx]


food_rag_store = FoodRagStore()
