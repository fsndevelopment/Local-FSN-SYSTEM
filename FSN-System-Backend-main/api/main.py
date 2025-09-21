"""
FSN Appium Farm - Main API Application

FastAPI server for Instagram automation farm management system.
Provides REST API for device management, account automation, job scheduling, and analytics.

Version: 1.2.0 - Fixed accounts database schema for cross-device sync
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time
from typing import Dict, Any

from core.config import settings
from database.connection import init_db
from routes import devices, accounts, jobs, content, tracking, system, real_device_test, websocket, account_switching, templates, models, warmup_templates, agents, device_fix, runs, job_websocket, photo_transfer, integrated_photo
# test_actions temporarily disabled due to FSM import complexity
from services.system_manager import system_manager
from services.device_pool_manager import device_pool_manager
from services.concurrent_job_executor import concurrent_job_executor
from services.websocket_manager import websocket_service
# from routes import schedules  # Temporarily disabled

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting FSN Appium Farm API", version=settings.app_version)
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Start automation services with multi-device support
        logger.info("🤖 Starting automation services with multi-device scaling...")
        
        # Initialize device pool manager
        await device_pool_manager.initialize()
        logger.info("📱 Device pool manager initialized")
        
        # Start concurrent job executor  
        await concurrent_job_executor.start()
        logger.info("🔥 Concurrent job executor started")
        
        # Start WebSocket service for real-time updates
        await websocket_service.start()
        logger.info("🔌 WebSocket service started")
        
        # Temporarily disable system manager to prevent job monitoring hang
        # await system_manager.start_all_services()
        logger.info("✅ Multi-device automation services started successfully")
        
        logger.info("🎉 FSN Appium Farm API started successfully")
        
    except Exception as e:
        logger.error("❌ Failed to start API server", error=str(e), exc_info=True)
        raise
    
    yield
    
    logger.info("🛑 Shutting down FSN Appium Farm API")
    try:
        # Stop WebSocket service
        await websocket_service.stop()
        logger.info("🔌 WebSocket service stopped")
        
        # Stop multi-device services
        await concurrent_job_executor.stop()
        logger.info("🔥 Concurrent job executor stopped")
        
        await system_manager.stop_all_services()
        logger.info("✅ All automation services stopped")
    except Exception as e:
        logger.error("❌ Error stopping services", error=str(e))
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Instagram automation farm management system with device control, account management, and analytics",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS - Allow all origins for now to fix the issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "📥 HTTP Request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "📤 HTTP Response",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "💥 HTTP Request Failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=f"{process_time:.3f}s",
            exc_info=True
        )
        raise


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """System health check endpoint"""
    from database.connection import get_db
    from sqlalchemy import text
    
    # Test database connection
    db_status = "unknown"
    try:
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            db_status = "connected" if result.scalar() == 1 else "error"
            break
    except Exception as e:
        logger.warning("Database health check failed", error=str(e))
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time(),
        "environment": "development" if settings.debug else "production",
        "database": db_status,
        "deployment": "v1.0.4-postgresql-fix"
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root() -> Dict[str, str]:
    """API root endpoint"""
    return {
        "message": f"{settings.app_name} is running with PostgreSQL",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
        "database": "PostgreSQL",
                "deployment": "v1.0.12-accounts-platform-fix"
    }


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        from init_database import init_database
        await init_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        raise

# Include API routes
app.include_router(devices.router, prefix=settings.api_v1_prefix, tags=["Devices"])
app.include_router(accounts.router, prefix=settings.api_v1_prefix, tags=["Accounts"])
app.include_router(jobs.router, prefix=settings.api_v1_prefix, tags=["Jobs"])
app.include_router(system.router, prefix=settings.api_v1_prefix, tags=["System"])
# app.include_router(schedules.router, prefix=settings.api_v1_prefix, tags=["Schedules"])  # Temporarily disabled
app.include_router(content.router, prefix=settings.api_v1_prefix, tags=["Content"])
app.include_router(tracking.router, prefix=settings.api_v1_prefix, tags=["Tracking"])
app.include_router(websocket.router, prefix=settings.api_v1_prefix, tags=["WebSocket"])
logger.info("🔌 WebSocket router registered at /api/v1/ws")
app.include_router(account_switching.router, prefix=settings.api_v1_prefix, tags=["Account Switching"])
app.include_router(templates.router, prefix=settings.api_v1_prefix, tags=["Templates"])
app.include_router(models.router, prefix=settings.api_v1_prefix, tags=["Models"])
app.include_router(warmup_templates.router, prefix=settings.api_v1_prefix, tags=["Warmup Templates"])
app.include_router(agents.router, prefix=settings.api_v1_prefix, tags=["Agents"])
app.include_router(device_fix.router, prefix=settings.api_v1_prefix, tags=["Device Fix"])
app.include_router(runs.router, prefix=settings.api_v1_prefix, tags=["Runs"])
app.include_router(job_websocket.router, prefix=settings.api_v1_prefix, tags=["Job WebSocket"])
logger.info("🔌 Job WebSocket router registered at /api/v1/jobs/ws")
# app.include_router(test_actions.router, tags=["Test Actions"])  # Temporarily disabled
app.include_router(real_device_test.router, tags=["Real Device Testing"])
app.include_router(photo_transfer.router, tags=["Photo Transfer"])
app.include_router(integrated_photo.router, tags=["Integrated Photo Posting"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(
        "💥 Unhandled Exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": str(int(time.time())),  # Simple error ID for tracking
        }
    )


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Endpoint {request.url.path} not found",
            "available_endpoints": "/docs" if settings.debug else "Contact administrator"
        }
    )


if __name__ == "__main__":
    import uvicorn
    import ssl
    import os
    
    logger.info("🔧 Starting development server")
    
    # Start server with HTTP (Render handles SSL)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,  # Use Render's PORT
        reload=False,  # Disable reload in production
        log_config=None  # Use structlog instead
    )
