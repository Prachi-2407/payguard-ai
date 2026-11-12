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

from extras.app.config import settings, mask_pii_in_text
from extras.app.database.session import init_db
from extras.app.analyzers.message_analyzer import get_message_model
from extras.app.analyzers.voice_analyzer import get_voice_model
from extras.app.api import health, messages, voice, community

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payguard.extras")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing PayGuard AI Extras database and preloading ML models...")
    init_db()
    # Preload models once at startup
    get_message_model()
    get_voice_model()
    logger.info("PayGuard AI Extras service startup complete on port %d.", settings.PORT)
    yield
    logger.info("Shutting down PayGuard AI Extras service...")

class NormalizePathMiddleware:
    """Normalizes duplicate slashes (e.g. '//api/ext/health' -> '/api/ext/health')."""
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
    description="PayGuard AI Extensions & Intelligence Layer (Message Scam Analysis, Voice Fraud Detection, Community Reputation)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(NormalizePathMiddleware)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Privacy-Preserving Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    raw_path = request.url.path
    raw_query = request.url.query
    masked_query = mask_pii_in_text(raw_query) if raw_query else ""
    query_str = f"?{masked_query}" if masked_query else ""
    masked_url = f"{raw_path}{query_str}"

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000.0
        logger.info(f"{request.method} {masked_url} -> {response.status_code} ({duration_ms:.1f}ms)")
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
    logger.exception("Unhandled extras service exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An internal server error occurred", "code": 500},
    )

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }

# Register API routers
app.include_router(health.router)
app.include_router(messages.router)
app.include_router(voice.router)
app.include_router(community.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("extras.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

