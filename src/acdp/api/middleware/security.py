"""OWASP Top 10 (2025/2026) & LLM10:2025 Security Hardening Middleware and Rate Limiting (TASK-SEC-01)."""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from acdp.api.db.models import User
from acdp.api.dependencies import get_current_user
from acdp.config import settings

logger = logging.getLogger(__name__)

_HIDDEN_PRODUCTION_PATHS = frozenset(
    {
        "/docs",
        "/docs/",
        "/docs/oauth2-redirect",
        "/redoc",
        "/redoc/",
        "/openapi.json",
    }
)
_AUTH_RATE_LIMITED_PATHS = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
    }
)


@dataclass(frozen=True)
class RateLimitDecision:
    """Result of evaluating a sliding-window rate limit check."""

    allowed: bool
    retry_after: int
    tier: str
    limit: int
    detail: str


class MultiTierRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter across AI, Auth, and Public tiers."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ai_user_minute: dict[str, deque[float]] = {}
        self._ai_user_day: dict[str, deque[float]] = {}
        self._ai_global_minute: deque[float] = deque()
        self._auth_ip_minute: dict[str, deque[float]] = {}
        self._public_ip_minute: dict[str, deque[float]] = {}
        self._total_checked = 0
        self._blocked_ai = 0
        self._blocked_auth = 0
        self._blocked_public = 0
        self._recent_blocks: deque[dict[str, Any]] = deque(maxlen=50)

    @staticmethod
    def _prune(window: deque[float], cutoff: float) -> None:
        while window and window[0] <= cutoff:
            window.popleft()

    @staticmethod
    def _retry_after(window: deque[float], window_seconds: float, now: float) -> int:
        if not window:
            return 1
        remaining = (window[0] + window_seconds) - now
        return max(1, math.ceil(remaining))

    def _record_block(self, tier: str, key: str, limit: int, retry_after: int) -> None:
        if tier.startswith("ai_"):
            self._blocked_ai += 1
        elif tier == "auth_ip_minute":
            self._blocked_auth += 1
        else:
            self._blocked_public += 1
        self._recent_blocks.append(
            {
                "tier": tier,
                "key": key,
                "limit": limit,
                "retry_after": retry_after,
                "timestamp": time.time(),
            }
        )

    def check_ai_limit(self, user_key: str) -> RateLimitDecision:
        """Enforce AI quota: 5/min/user, 30/day/user, and 10 RPM global before LLM/Qdrant invocation."""
        if not settings.rate_limit_enabled:
            return RateLimitDecision(True, 0, "ai_disabled", 0, "")

        now = time.monotonic()
        user_min_limit = settings.rate_limit_ai_per_minute
        user_day_limit = settings.rate_limit_ai_per_day
        global_rpm_limit = settings.rate_limit_ai_global_rpm

        with self._lock:
            self._total_checked += 1
            user_min_win = self._ai_user_minute.setdefault(user_key, deque())
            user_day_win = self._ai_user_day.setdefault(user_key, deque())

            self._prune(user_min_win, now - 60.0)
            self._prune(user_day_win, now - 86400.0)
            self._prune(self._ai_global_minute, now - 60.0)

            if len(user_min_win) >= user_min_limit:
                retry = self._retry_after(user_min_win, 60.0, now)
                self._record_block("ai_user_minute", user_key, user_min_limit, retry)
                return RateLimitDecision(
                    allowed=False,
                    retry_after=retry,
                    tier="ai_user_minute",
                    limit=user_min_limit,
                    detail=f"AI rate limit exceeded ({user_min_limit} requests/minute per user). Retry in {retry}s.",
                )

            if len(user_day_win) >= user_day_limit:
                retry = self._retry_after(user_day_win, 86400.0, now)
                self._record_block("ai_user_day", user_key, user_day_limit, retry)
                return RateLimitDecision(
                    allowed=False,
                    retry_after=retry,
                    tier="ai_user_day",
                    limit=user_day_limit,
                    detail=f"Daily AI quota exceeded ({user_day_limit} requests/day per user). Retry in {retry}s.",
                )

            if len(self._ai_global_minute) >= global_rpm_limit:
                retry = self._retry_after(self._ai_global_minute, 60.0, now)
                self._record_block("ai_global_rpm", "global", global_rpm_limit, retry)
                return RateLimitDecision(
                    allowed=False,
                    retry_after=retry,
                    tier="ai_global_rpm",
                    limit=global_rpm_limit,
                    detail=f"Global AI capacity limit reached ({global_rpm_limit} RPM). Retry in {retry}s.",
                )

            user_min_win.append(now)
            user_day_win.append(now)
            self._ai_global_minute.append(now)
            return RateLimitDecision(True, 0, "ai_ok", user_min_limit, "")

    def check_auth_limit(self, client_ip: str) -> RateLimitDecision:
        """Enforce brute-force protection on /auth/login & /auth/register (10 req/min/IP)."""
        return self._check_ip_window(
            buckets=self._auth_ip_minute,
            client_ip=client_ip,
            limit=settings.rate_limit_auth_per_minute,
            tier="auth_ip_minute",
            detail_prefix="Too many authentication attempts",
        )

    def check_public_limit(self, client_ip: str) -> RateLimitDecision:
        """Enforce general API rate limit (60 req/min/IP) for /api/v1/* routes."""
        return self._check_ip_window(
            buckets=self._public_ip_minute,
            client_ip=client_ip,
            limit=settings.rate_limit_public_per_minute,
            tier="public_ip_minute",
            detail_prefix="Too many requests",
        )

    def _check_ip_window(
        self,
        *,
        buckets: dict[str, deque[float]],
        client_ip: str,
        limit: int,
        tier: str,
        detail_prefix: str,
    ) -> RateLimitDecision:
        if not settings.rate_limit_enabled:
            return RateLimitDecision(True, 0, tier, 0, "")

        now = time.monotonic()
        with self._lock:
            self._total_checked += 1
            win = buckets.setdefault(client_ip, deque())
            self._prune(win, now - 60.0)
            if len(win) >= limit:
                retry = self._retry_after(win, 60.0, now)
                self._record_block(tier, client_ip, limit, retry)
                return RateLimitDecision(
                    allowed=False,
                    retry_after=retry,
                    tier=tier,
                    limit=limit,
                    detail=f"{detail_prefix} ({limit} requests/minute per IP). Retry in {retry}s.",
                )
            win.append(now)
            return RateLimitDecision(True, 0, tier, limit, "")

    def stats(self) -> dict[str, Any]:
        """Return security rate-limiting telemetry for monitoring and /admin inspection."""
        with self._lock:
            return {
                "enabled": settings.rate_limit_enabled,
                "limits": {
                    "ai_per_minute": settings.rate_limit_ai_per_minute,
                    "ai_per_day": settings.rate_limit_ai_per_day,
                    "ai_global_rpm": settings.rate_limit_ai_global_rpm,
                    "auth_per_minute": settings.rate_limit_auth_per_minute,
                    "public_per_minute": settings.rate_limit_public_per_minute,
                },
                "total_checked": self._total_checked,
                "blocked_ai": self._blocked_ai,
                "blocked_auth": self._blocked_auth,
                "blocked_public": self._blocked_public,
                "recent_blocks": list(self._recent_blocks),
            }

    def reset(self) -> None:
        """Clear all rate limit windows and counters (used in tests and admin resets)."""
        with self._lock:
            self._ai_user_minute.clear()
            self._ai_user_day.clear()
            self._ai_global_minute.clear()
            self._auth_ip_minute.clear()
            self._public_ip_minute.clear()
            self._total_checked = 0
            self._blocked_ai = 0
            self._blocked_auth = 0
            self._blocked_public = 0
            self._recent_blocks.clear()


rate_limiter = MultiTierRateLimiter()


def get_rate_limit_stats() -> dict[str, Any]:
    """Return global MultiTierRateLimiter telemetry."""
    return rate_limiter.stats()


def reset_rate_limiter() -> None:
    """Reset global MultiTierRateLimiter state."""
    rate_limiter.reset()


def extract_client_ip(request: Request) -> str:
    """Resolve client IP from X-Forwarded-For or ASGI client tuple."""
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        first_ip = forwarded_for.split(",", 1)[0].strip()
        if first_ip:
            return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


async def enforce_ai_rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> None:
    """FastAPI dependency enforcing per-user and global RPM limits on AI RAG routes (LLM10:2025)."""
    decision = rate_limiter.check_ai_limit(str(current_user.id))
    if not decision.allowed:
        logger.warning(
            "Security Event [429]: tier=%s user_id=%s ip=%s path=%s retry_after=%s",
            decision.tier,
            current_user.id,
            extract_client_ip(request),
            request.url.path,
            decision.retry_after,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=decision.detail,
            headers={
                "Retry-After": str(decision.retry_after),
                "X-RateLimit-Tier": decision.tier,
                "X-RateLimit-Limit": str(decision.limit),
            },
        )


def apply_security_headers(
    response: Response,
    *,
    path: str = "",
    is_production: bool = False,
) -> Response:
    """Attach OWASP Top 10 security headers to every HTTP response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "0"

    if path.startswith(("/docs", "/redoc", "/api/v1/admin/docs")):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; frame-ancestors 'none'",
        )
    else:
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'",
        )

    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    return response


def _masked_internal_error_response(*, path: str, is_production: bool) -> JSONResponse:
    """Return sanitized HTTP 500 JSON without leaking tracebacks or internal config (OWASP A10:2025)."""
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )
    return apply_security_headers(response, path=path, is_production=is_production)


class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """Unified ASGI middleware for /docs hiding, IP rate limiting, exception masking, and headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        is_prod = settings.is_production

        if path in _HIDDEN_PRODUCTION_PATHS:
            resp = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Not Found"},
            )
            return apply_security_headers(resp, path=path, is_production=is_prod)

        if request.method != "OPTIONS" and path.startswith("/api/v1/") and path != "/api/v1/health":
            client_ip = extract_client_ip(request)
            if path in _AUTH_RATE_LIMITED_PATHS and request.method == "POST":
                decision = rate_limiter.check_auth_limit(client_ip)
            else:
                decision = rate_limiter.check_public_limit(client_ip)

            if not decision.allowed:
                logger.warning(
                    "Security Event [429]: tier=%s ip=%s method=%s path=%s retry_after=%s",
                    decision.tier,
                    client_ip,
                    request.method,
                    path,
                    decision.retry_after,
                )
                resp = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": decision.detail,
                        "tier": decision.tier,
                        "retry_after": decision.retry_after,
                    },
                    headers={
                        "Retry-After": str(decision.retry_after),
                        "X-RateLimit-Tier": decision.tier,
                        "X-RateLimit-Limit": str(decision.limit),
                    },
                )
                return apply_security_headers(resp, path=path, is_production=is_prod)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled server exception on %s %s", request.method, path)
            return _masked_internal_error_response(path=path, is_production=is_prod)

        return apply_security_headers(response, path=path, is_production=is_prod)


def register_security_exception_handlers(app: FastAPI) -> None:
    """Register global exception masking handler on FastAPI app (OWASP A10:2025)."""

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled FastAPI exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return _masked_internal_error_response(
            path=request.url.path,
            is_production=settings.is_production,
        )
