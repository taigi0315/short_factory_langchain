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

from fastapi import status
from fastapi.responses import JSONResponse

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

app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(dev.router, prefix="/api/dev", tags=["dev"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8001, reload=True)
