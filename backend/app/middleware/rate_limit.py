import asyncio
import math
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


EXEMPT_PATHS = {"/", "/health"}


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or "unknown"

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


class _InMemorySlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1, window_seconds)
        self._requests_by_ip: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check_request(self, client_ip: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            requests = self._requests_by_ip[client_ip]
            while requests and requests[0] <= cutoff:
                requests.popleft()

            if len(requests) >= self.max_requests:
                retry_after = max(1, math.ceil((requests[0] + self.window_seconds) - now))
                return False, retry_after

            requests.append(now)
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool,
        requests: int,
        window_seconds: int,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self._limiter = _InMemorySlidingWindowLimiter(
            max_requests=requests,
            window_seconds=window_seconds,
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in EXEMPT_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        is_allowed, retry_after = await self._limiter.check_request(client_ip)
        if is_allowed:
            return await call_next(request)

        return JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests"},
            headers={"Retry-After": str(retry_after)},
        )
