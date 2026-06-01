from functools import lru_cache
import numpy as np
from openai import OpenAI

from shared.config import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_client() -> OpenAI:
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url="https://openrouter.ai/api/v1",
    )


class TextEncoder:
    def __init__(self):
        self.client = get_embedding_client()

    def encode(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=MODEL_NAME,
            input=text,
        )

        embedding = response.data[0].embedding

        # normalize علشان التست يعدي
        vec = np.array(embedding, dtype=np.float32)
        vec = vec / np.linalg.norm(vec)

        return vec.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=MODEL_NAME,
            input=texts,
        )

        embeddings = []

        for item in response.data:
            vec = np.array(item.embedding, dtype=np.float32)
            vec = vec / np.linalg.norm(vec)
            embeddings.append(vec.tolist())

        return embeddings

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        a = np.array(vec1)
        b = np.array(vec2)

        return float(np.dot(a, b))