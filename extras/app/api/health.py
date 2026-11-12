from fastapi import APIRouter
from extras.app.schemas.models import HealthResponse

router = APIRouter(prefix="/api/ext", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Service health check endpoint."""
    return HealthResponse(status="ok")

