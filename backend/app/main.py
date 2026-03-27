from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import the new metrics router
from app.metrics import router as metrics_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Cost Optimizer API",
    description="API for AWS cost optimization and resource metrics",
    version="1.0.0"
)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include metrics router
app.include_router(metrics_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cost Optimizer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/api/metrics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cost-optimizer-backend"
    }


@app.get("/api/dashboard/summary")
async def dashboard_summary():
    """Dashboard summary endpoint"""
    return {
        "message": "Dashboard summary",
        "status": "active"
    }