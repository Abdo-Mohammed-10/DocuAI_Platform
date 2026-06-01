from functools import lru_cache

from langchain_openai import OpenAIEmbeddings


from langchain_openai import ChatOpenAI

from shared.config import settings

embeddings = OpenAIEmbeddings(
    model="sentence-transformers/paraphrase-minilm-l6-v2",
    api_key=settings.openai_api_key,
    base_url="https://openrouter.ai/api/v1"
)


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
        model="sentence-transformers/paraphrase-minilm-l6-v2",
        api_key=settings.openai_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
