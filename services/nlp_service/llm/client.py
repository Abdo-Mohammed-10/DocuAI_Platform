from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

from shared.config import settings


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model="openai/gpt-oss-20b",
        temperature=temperature,
        api_key=settings.openai_api_key,
        base_url="https://openrouter.ai/api/v1",
        max_retries=3,
    )

@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )