"""API key authentication middleware for the DEMON server."""

from __future__ import annotations

import logging
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt
from OpenDEMON.server.auth_routes import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates ``Authorization: Bearer <key>`` on ``/v1/*`` and ``/api/*`` routes.

    Webhook routes and health checks are exempt — they use
    per-channel signature verification instead.
    """

    def __init__(
        self,
        app,
        api_key: str = "",
        base_seconds: int = 2,
        max_seconds: int = 60,
    ) -> None:  # noqa: ANN001
        super().__init__(app)
        self._api_key = api_key or os.environ.get("DEMON_API_KEY", "")
        self._base_seconds = base_seconds
        self._max_seconds = max_seconds
        self._failed_attempts: dict[str, dict] = {}

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if self._requires_auth(request.url.path):
            client_ip = request.client.host if request.client else "unknown"
            
            import time
            now = time.time()
            auth = request.headers.get("Authorization", "")
            
            # When no API key is configured (local/loopback mode) and no auth header is provided,
            # allow standard endpoints through.
            if not auth:
                if not self._api_key:
                    return await call_next(request)
                return JSONResponse(
                    {"detail": "Missing Authorization header"},
                    status_code=401,
                )

            # Check lockout for auth attempts
            is_loopback = client_ip in ("127.0.0.1", "localhost", "::1", "unknown")
            record = self._failed_attempts.get(client_ip)
            lockout = record.get("lockout_until", 0) if record else 0
            if lockout and now < lockout and not (is_loopback and not self._api_key):
                return JSONResponse(
                    {"detail": "Too many failed attempts. Try again later."},
                    status_code=429,
                    headers={"Retry-After": str(max(1, int(lockout - now)))},
                )

            if not auth.startswith("Bearer "):
                # Track failed attempts
                attempt = self._failed_attempts.get(client_ip, {"count": 0, "last": 0, "lockout_until": 0})
                if now - attempt.get("last", 0) > self._max_seconds:
                    attempt["count"] = 0
                attempt["count"] += 1
                attempt["last"] = now
                if attempt["count"] >= 5:
                    attempt["lockout_until"] = now + self._max_seconds
                self._failed_attempts[client_ip] = attempt
                return JSONResponse({"detail": "Missing credentials"}, status_code=401)

            token = auth[7:]
            
            # 1. Check if it's the static API key
            if self._api_key and secrets.compare_digest(token, self._api_key):
                if client_ip in self._failed_attempts:
                    del self._failed_attempts[client_ip]
                return await call_next(request)
                
            # 2. Check if it's a valid JWT token
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                request.state.user_id = payload.get("sub")
                if client_ip in self._failed_attempts:
                    del self._failed_attempts[client_ip]
                return await call_next(request)
            except jwt.ExpiredSignatureError:
                return JSONResponse({"detail": "Token expired"}, status_code=401)
            except jwt.PyJWTError:
                pass  # Fall through to failure handling
                
            # Track failed attempts for invalid tokens
            attempt = self._failed_attempts.get(client_ip, {"count": 0, "last": 0, "lockout_until": 0})
            if now - attempt.get("last", 0) > self._max_seconds:
                attempt["count"] = 0
            attempt["count"] += 1
            attempt["last"] = now
            if attempt["count"] >= 5:
                attempt["lockout_until"] = now + self._max_seconds
            self._failed_attempts[client_ip] = attempt
            
            return JSONResponse(
                {"detail": "Invalid credentials"},
                status_code=401,
            )

        return await call_next(request)

    @staticmethod
    def _requires_auth(path: str) -> bool:
        """Protect API routes and operational metrics; leave the UI/health open."""
        # Public auth routes don't require authentication (except /me)
        if path.startswith("/v1/auth/") and path != "/v1/auth/me":
            return False
            
        return (
            path.startswith("/v1/")
            or path.startswith("/api/")
            or path == "/metrics"
            or path.startswith("/metrics/")
        )



def generate_api_key() -> str:
    """Generate a new API key with ``oj_sk_`` prefix."""
    return f"oj_sk_{secrets.token_urlsafe(32)}"


def check_bind_safety(host: str, *, api_key: str) -> None:
    """Refuse to bind non-loopback without an API key.

    Raises ``SystemExit`` if *host* is not a loopback address and
    *api_key* is empty.
    """
    import ipaddress
    import sys

    try:
        is_loop = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loop = host in ("localhost", "")

    if not is_loop and not api_key:
        logger.error(
            "Binding to %s requires DEMON_API_KEY to be set. "
            "Run: DEMON auth generate-key",
            host,
        )
        sys.exit(1)


def websocket_authorized(websocket, expected_key: str) -> bool:  # noqa: ANN001
    """Return ``True`` if a WebSocket connection presents the expected key.

    ``AuthMiddleware`` is a ``BaseHTTPMiddleware`` and never sees WebSocket
    upgrade requests, so streaming endpoints must check the token themselves
    in the handshake before calling ``websocket.accept()``.

    When *expected_key* is empty, authentication is disabled (the loopback /
    local-only default, matching :class:`AuthMiddleware`) and all connections
    are allowed. The token may be supplied either as a ``?token=`` query
    parameter — browsers cannot set headers on a WebSocket handshake — or via
    an ``Authorization: Bearer <key>`` header for programmatic clients.
    """
    if not expected_key:
        return True
    token = websocket.query_params.get("token", "")
    if not token:
        auth = websocket.headers.get("authorization", "")
        scheme, _, value = auth.partition(" ")
        if scheme.lower() == "bearer":
            token = value
    if not token:
        return False
    return secrets.compare_digest(token, expected_key)
