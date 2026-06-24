from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from shared.config import settings

from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from shared.config import settings

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  


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
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.openai_api_key,
        base_url="https://openrouter.ai/api/v1",
    )