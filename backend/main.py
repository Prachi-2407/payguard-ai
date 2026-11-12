import time
import re
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.db.session import init_db
from backend.analyzers.url_analyzer import get_url_model
from backend.analyzers.txn_analyzer import get_txn_model
from backend.routers import analyze, history, health

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payguard")

def mask_sensitive_query(text: str) -> str:
    """Masks query parameters to prevent logging sensitive user tokens / IDs in plain text."""
    return re.sub(r'([?&][^=]+=)[^&\s]+', r'\1***', text)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing PayGuard AI database and ML models...")
    init_db()
    # Preload ML models once at startup
    get_url_model()
    get_txn_model()
    logger.info("PayGuard AI service startup complete.")
    yield
    logger.info("Shutting down PayGuard AI...")

class NormalizePathMiddleware:
    """Normalizes duplicate slashes (e.g. '//api/health' -> '/api/health') to prevent 404s."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if "//" in path:
                scope["path"] = re.sub(r"/+", "/", path)
        await self.app(scope, receive, send)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Intelligent Payment Fraud Prevention Engine for UPI & Digital Transactions",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(NormalizePathMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Privacy-Preserving Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    raw_path = request.url.path
    raw_query = request.url.query
    query_str = f"?{mask_sensitive_query(raw_query)}" if raw_query else ""
    masked_url = f"{raw_path}{query_str}"

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000.0
        logger.info(
            f"{request.method} {masked_url} -> {response.status_code} ({duration_ms:.1f}ms)"
        )
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000.0
        logger.error(f"{request.method} {masked_url} FAILED in {duration_ms:.1f}ms: {e}")
        raise

# Contract-Compliant Error Handlers: { "error": "message", "code": 400 }
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        msg = err.get("msg", "Invalid input")
        error_messages.append(f"{field}: {msg}" if field else msg)

    full_error = "; ".join(error_messages) or "Invalid request parameters"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": full_error, "code": 400},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "code": exc.status_code},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An internal server error occurred", "code": 500},
    )

# Register routers
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }

app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
