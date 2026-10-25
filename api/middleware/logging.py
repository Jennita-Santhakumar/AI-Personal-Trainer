"""
api/middleware/logging.py — structured request logging with structlog.

Fix: Wrap call_next in try/except so exceptions are still logged before
     being re-raised. Without this, a 500 from inside the stack never
     gets a log line showing method/path/status.
"""
import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=status_code,
                duration_ms=duration_ms,
                user_agent=request.headers.get("user-agent", ""),
            )
