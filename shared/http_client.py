import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def post_json(url: str, json: dict, headers: dict | None = None):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url,
            json=json,
            headers=headers,
        )

        response.raise_for_status()

        return response