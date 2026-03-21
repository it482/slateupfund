"""FastAPI application entry point."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from backend import config
from backend.exceptions import BoldSignServiceError
from backend.routes.documents import router as documents_router

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = config.get_settings()
    if not settings.debug:
        # Do not raise here: a failed lifespan prevents the server from binding to PORT,
        # which Cloud Run reports as "container failed to listen on PORT=8080". Log and
        # continue so /health works; document routes still enforce keys via dependencies.
        if not settings.boldsign_api_key:
            logger.critical(
                "BOLDSIGN_API_KEY is not set (DEBUG=false). "
                "Set it in the Cloud Run service environment (or .env locally). "
                "BoldSign document endpoints will fail until it is configured."
            )
        if not settings.api_key:
            logger.critical(
                "API_KEY is not set (DEBUG=false). "
                "Set it in the Cloud Run service environment (or .env locally). "
                "Authenticated routes will reject requests until it is configured."
            )
    elif not settings.boldsign_api_key or not settings.api_key:
        logger.warning(
            "BOLDSIGN_API_KEY or API_KEY not set. "
            "Document endpoints may fail. Set DEBUG=false in production."
        )
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    yield


def _get_cors_config() -> tuple[list[str], bool]:
    """
    Parse CORS_ORIGINS and whether credentials are allowed.

    Wildcard origin (*) must not be combined with allow_credentials=True (browser security).
    """
    settings = config.get_settings()
    if settings.cors_origins:
        origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
        return origins, True
    if settings.debug:
        return ["*"], False
    return [], False


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = config.get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json",
    )

    @app.exception_handler(BoldSignServiceError)
    async def boldsign_service_error_handler(_request: Request, exc: BoldSignServiceError):
        return JSONResponse(
            status_code=400,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )

    app.state.limiter = limiter
    limiter.application_limits = [settings.rate_limit]
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    cors_origins, cors_credentials = _get_cors_config()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Health check for load balancers and monitoring."""
        return {"status": "ok"}

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log request method, path, response status, and duration (no secrets)."""
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s %s %.2fms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s error %.2fms: %s",
                request.method,
                request.url.path,
                duration_ms,
                exc,
            )
            raise

    app.include_router(documents_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.get_settings().debug,
    )
