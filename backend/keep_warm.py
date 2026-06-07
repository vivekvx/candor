"""
Keep-warm script to prevent Railway free tier cold starts.
Run this as a separate process or cron job.
Pings the backend every 10 minutes to keep it warm.
"""
import asyncio
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://your-railway-url.railway.app"
)
PING_INTERVAL_SECONDS = 600  # 10 minutes


async def ping_backend() -> bool:
    """
    Ping the backend health endpoint.
    Returns True if backend is warm and responding.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/ping",
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as error:
        logger.warning(f"Ping failed: {error}")
        return False


async def keep_warm_loop():
    """Continuously ping backend to prevent cold starts."""
    logger.info(f"Starting keep-warm for {BACKEND_URL}")
    while True:
        is_warm = await ping_backend()
        status = "warm" if is_warm else "cold/unreachable"
        logger.info(f"Backend status: {status}")
        await asyncio.sleep(PING_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(keep_warm_loop())
