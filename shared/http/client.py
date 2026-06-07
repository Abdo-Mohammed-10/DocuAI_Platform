import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def post_with_retry(url, **kwargs):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, **kwargs)
        response.raise_for_status()
        return response