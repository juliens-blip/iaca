from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional Bearer token middleware.

    If api_auth_token is empty, all requests pass through.
    If api_auth_token is set, all mutation (POST/PUT/PATCH/DELETE) requests
    under /api/ require a valid Authorization: Bearer <token> header.
    """

    async def dispatch(self, request: Request, call_next):
        token = settings.api_auth_token
        if not token:
            return await call_next(request)

        # WebSocket upgrades are GET requests with Upgrade: websocket header.
        # Auth is handled inside the WS handler itself (close code 1008).
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        if request.method in MUTATION_METHODS and request.url.path.startswith("/api/"):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: invalid or missing Bearer token"},
                )

        return await call_next(request)


async def verify_ws_token(token_param: str | None, auth_header: str | None) -> bool:
    """Verify WebSocket token from query param or Authorization header.

    Returns True if auth is valid (or not required), False otherwise.
    """
    required_token = settings.api_auth_token
    if not required_token:
        return True

    # Check query param first, then header
    if token_param and token_param == required_token:
        return True
    if auth_header and auth_header.startswith("Bearer ") and auth_header[7:] == required_token:
        return True

    return False
