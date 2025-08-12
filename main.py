from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

# Import custom modules
from app.api.routes import router as api_router
from app.core.config import settings
from app.core.dependencies import get_current_timestamp

# Configure logging for production-ready error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    This is where you'd initialize databases, cache connections, etc.
    """
    # Startup
    logger.info("🚀 Kenya Startup Navigator API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Kenya Startup Navigator API shutting down...")


# Create FastAPI application with comprehensive metadata
app = FastAPI(
    title="Kenya Startup Ecosystem Navigator API",
    description="""
    🚀 **Intelligent Q&A System for Kenya's Startup Ecosystem**
    
    This API provides AI-powered insights and guidance for entrepreneurs navigating
    Kenya's startup landscape. Features include:
    
    - **Smart Query Processing**: AI-powered responses to ecosystem questions
    - **Investor Matching**: Intelligent matching between startups and funding sources
    - **Ecosystem Intelligence**: Comprehensive database of Kenya's startup resources
    - **Personalized Guidance**: Tailored advice based on startup profiles
    
    ## Key Endpoints
    - `/api/v1/query` - Submit questions and get AI responses
    - `/api/v1/startups/profile` - Manage startup profiles
    - `/api/v1/ecosystem/investors` - Access investor database
    - `/api/v1/ecosystem/accelerators` - Find accelerators and incubators
    
    ## Authentication
    Currently open access for demo purposes. Production would include API key authentication.
    """,
    version="1.0.0",
    contact={
        "name": "Kenya Startup Navigator Team",
        "email": "contact@kenyastartupnav.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    # Custom documentation URLs for professional appearance
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Middleware - Essential for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Configure based on environment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware for production deployment
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Global exception handler for professional error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Custom HTTP exception handler that returns user-friendly error messages
    This makes your API feel professional and helps with debugging
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": get_current_timestamp(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """
    Catch-all exception handler for unexpected errors
    In production, you'd log these to monitoring services like Sentry
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "timestamp": get_current_timestamp(),
            "path": str(request.url.path)
        }
    )


# Health check endpoint - essential for deployment platforms
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring and deployment platforms
    Returns basic system status and configuration info
    """
    return {
        "status": "healthy",
        "service": "Kenya Startup Navigator API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": get_current_timestamp(),
        "features": {
            "ai_integration": True,
            "ecosystem_database": True,
            "investor_matching": True,
            "startup_profiling": True
        }
    }


# Root endpoint with API information
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint providing API overview and navigation links
    """
    return {
        "message": "🚀 Welcome to Kenya Startup Ecosystem Navigator API",
        "description": "AI-powered guidance for Kenya's startup ecosystem",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": "/api/docs",
            "redoc": "/api/redoc"
        },
        "endpoints": {
            "health_check": "/health",
            "api_base": "/api/v1",
            "query_ai": "/api/v1/query",
            "ecosystem": "/api/v1/ecosystem"
        },
        "github": "https://github.com/yourusername/kenya-startup-navigator",
        "timestamp": get_current_timestamp()
    }


# Include API routes with version prefix
app.include_router(
    api_router, 
    prefix="/api/v1", 
    tags=["API v1"]
)


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,  # Auto-reload in development
        log_level="info"
    )
    