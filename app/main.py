"""
Main FastAPI Application
Deep Learning Threat Intelligence with Text GNN and Image ViT
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

from .routes import training_router, onion_router, prediction_router
from .models.deep_learning import deep_learning_manager
from .config import Config

# Create directories
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.TEXT_UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.IMAGE_UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.ONION_UPLOAD_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)

app = FastAPI(
    title="Cyber Threat Intelligence API",
    description="Deep Learning: Text GNN + Image ViT for Threat Detection",
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


@app.on_event("startup")
async def startup_event():
    """Load trained deep learning models on startup"""
    print("\n" + "="*70)
    print("🚀 Starting Deep Learning Threat Intelligence API")
    print("="*70)
    
    print("\n📦 Loading Deep Learning Models...")
    deep_learning_manager.load_text_gnn(Config.TEXT_MODEL_PATH)
    deep_learning_manager.load_image_vit(Config.IMAGE_MODEL_PATH)
    
    print("\n📊 Deep Learning Model Status:")
    print(f"   Text GNN (Graph Neural Network): {'✅ Loaded' if deep_learning_manager.text_model_loaded else '❌ Not trained'}")
    print(f"   Image ViT (Vision Transformer): {'✅ Loaded' if deep_learning_manager.image_model_loaded else '❌ Not trained'}")
    print("="*70 + "\n")


@app.get("/")
async def root():
    return {
        "message": "Deep Learning Threat Intelligence API",
        "status": "running",
        "version": "2.0.0",
        "deep_learning_models": {
            "text_gnn": {
                "loaded": deep_learning_manager.text_model_loaded,
                "architecture": "Graph Neural Network",
                "classes": ["gun", "drug", "poison"]
            },
            "image_vit": {
                "loaded": deep_learning_manager.image_model_loaded,
                "architecture": "Vision Transformer",
                "classes": ["drugs", "firearms", "poison"]
            }
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}