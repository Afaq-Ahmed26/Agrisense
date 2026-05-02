from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.routes import auth, users, sensors, irrigation, ml, alerts, notifications, activity_logs, thresholds, reports, middleman

# Create FastAPI app instance
app = FastAPI(
    title="AgriSense Backend API",
    description="Smart Irrigation System API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://192.168.100.18:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(middleman.router, prefix="/middleman", tags=["middleman"])
app.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
app.include_router(irrigation.router, prefix="/irrigation", tags=["irrigation"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(activity_logs.router, prefix="/activity-logs", tags=["activity logs"])
app.include_router(thresholds.router, prefix="/thresholds", tags=["thresholds"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgriSense Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agrisense-backend"}
