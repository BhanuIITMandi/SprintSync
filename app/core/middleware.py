import time
import json
import logging
import traceback
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt, JWTError
import os

logger = logging.getLogger("sprintsync")

# ─── In-memory metrics store ───

_metrics = {
    "http_requests_total": defaultdict(int),       # key: (method, path, status)
    "http_request_duration_seconds": [],            # list of (method, path, duration)
}


def get_metrics_store():
    return _metrics


# ─── Middleware ───

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        user_id = self._extract_user_id(request)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start
            self._log_request(request, 500, duration, user_id, error=exc)
            self._record_metric(request, 500, duration)
            raise

        duration = time.perf_counter() - start
        self._log_request(request, response.status_code, duration, user_id)
        self._record_metric(request, response.status_code, duration)
        return response

    @staticmethod
    def _extract_user_id(request: Request) -> str | None:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:]
        try:
            secret = os.getenv("SECRET_KEY", "super-secret-key")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return payload.get("sub")
        except JWTError:
            return None

    @staticmethod
    def _log_request(
        request: Request,
        status_code: int,
        duration: float,
        user_id: str | None,
        error: Exception | None = None,
    ):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "method": request.method,
            "path": str(request.url.path),
            "userId": user_id,
            "status_code": status_code,
            "latency_ms": round(duration * 1000, 2),
        }

        if error or status_code >= 500:
            log_entry["error"] = str(error) if error else "Internal Server Error"
            log_entry["stacktrace"] = traceback.format_exc()
            logger.error(json.dumps(log_entry))
        else:
            logger.info(json.dumps(log_entry))

    @staticmethod
    def _record_metric(request: Request, status_code: int, duration: float):
        path = str(request.url.path)
        method = request.method
        _metrics["http_requests_total"][(method, path, status_code)] += 1
        _metrics["http_request_duration_seconds"].append((method, path, duration))
