from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cost Optimizer API",
    description="AWS Cloud Resource Cost Optimization API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Cost Optimizer API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cost-optimizer-backend"
    }

@app.get("/api/dashboard/summary")
async def dashboard_summary():
    return {
        "current_month_cost": 0.00,
        "projected_cost": 0.00,
        "potential_savings": 0.00,
        "optimization_score": 0
    }
