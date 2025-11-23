from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from src.core.config import settings
from src.core.logging import configure_logging

# Configure logging
logger = configure_logging()

app = FastAPI(
    title="ShortFactory API",
    description="API for ShortFactoryLangChain video generation platform",
    version="1.0.0"
)

# Middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure all HTTP exceptions return JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return JSON."""
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {type(exc).__name__}",
            "message": str(exc) if settings.DEV_MODE else "An error occurred"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    # Check critical dependencies
    checks = {
        "status": "healthy",
        "services": {
            "storage": "ok",
        }
    }
    
    # Verify API keys are set if real mode is enabled
    if settings.USE_REAL_LLM and not settings.GEMINI_API_KEY:
        checks["status"] = "unhealthy"
        checks["errors"] = ["GEMINI_API_KEY not set"]
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=checks
        )
    
    return checks

from src.api.routes import stories, scripts, dev
from fastapi.staticfiles import StaticFiles
import os

# Create generated_assets directory if it doesn't exist
os.makedirs("generated_assets", exist_ok=True)

# Mount static files
app.mount("/generated_assets", StaticFiles(directory="generated_assets"), name="generated_assets")

# Import routers
from src.api.routes import stories, scripts, dev, scene_editor

app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(dev.router, prefix="/api/dev", tags=["dev"])
app.include_router(scene_editor.router)  # Already has prefix in router definition

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8001, reload=True)
