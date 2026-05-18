from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

# Import routes
from app.routes import training_router, onion_router, prediction_router

# Create directories
os.makedirs("uploads/text", exist_ok=True)
os.makedirs("uploads/images/drugs", exist_ok=True)
os.makedirs("uploads/images/firearms", exist_ok=True)
os.makedirs("uploads/images/poison", exist_ok=True)
os.makedirs("models", exist_ok=True)

app = FastAPI(
    title="Cyber Threat Intelligence API",
    description="Deep Learning driven CTI application with GCN and ViT",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(training_router)
app.include_router(onion_router)
app.include_router(prediction_router)

@app.get("/")
async def root():
    return {
        "message": "Cyber Threat Intelligence API",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)