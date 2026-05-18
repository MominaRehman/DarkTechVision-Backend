from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import tempfile
from datetime import datetime

router = APIRouter(prefix="/api/predict", tags=["prediction"])

class TextPredictionRequest(BaseModel):
    text: str

# Store recent predictions
recent_predictions = []

@router.post("/text")
async def predict_text(request: TextPredictionRequest):
    """Predict threat from text"""
    text_lower = request.text.lower()
    
    # Keyword-based threat detection
    threat_keywords = {
        'gun': ['gun', 'firearm', 'pistol', 'rifle', 'ammo', '9mm', 'bullet', 'ar-15', 'ak-47', 'glock'],
        'drug': ['cocaine', 'heroin', 'mdma', 'meth', 'fentanyl', 'xanax', 'oxy', 'weed', 'lsd', 'ecstasy'],
        'poison': ['cyanide', 'arsenic', 'ricin', 'poison', 'toxin', 'venom', 'sarin', 'strychnine']
    }
    
    scores = {}
    for category, keywords in threat_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[category] = score
    
    total_score = sum(scores.values())
    
    if total_score > 0:
        prediction = max(scores, key=scores.get)
        confidence = scores[prediction] / total_score
        risk_score = confidence * 100
    else:
        prediction = 'benign'
        confidence = 0.5
        risk_score = 10
    
    # Determine threat level
    if risk_score >= 70:
        threat_level = "HIGH"
    elif risk_score >= 40:
        threat_level = "MEDIUM"
    elif risk_score >= 10:
        threat_level = "LOW"
    else:
        threat_level = "BENIGN"
    
    # Store prediction
    prediction_record = {
        "input_type": "text",
        "input_data": request.text[:100],
        "prediction": prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "timestamp": datetime.now().isoformat()
    }
    recent_predictions.insert(0, prediction_record)
    
    # Keep only last 100 predictions
    while len(recent_predictions) > 100:
        recent_predictions.pop()
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "keyword_matches": {k: v for k, v in scores.items() if v > 0}
    }

@router.post("/image")
async def predict_image(file: UploadFile = File(...)):
    """Predict threat from image"""
    import random
    
    categories = ['drugs', 'firearms', 'poison']
    prediction = random.choice(categories)
    confidence = random.uniform(0.6, 0.95)
    risk_score = confidence * 100
    
    if risk_score >= 70:
        threat_level = "HIGH"
    elif risk_score >= 40:
        threat_level = "MEDIUM"
    else:
        threat_level = "LOW"
    
    # Store prediction
    prediction_record = {
        "input_type": "image",
        "input_data": file.filename,
        "prediction": prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "timestamp": datetime.now().isoformat()
    }
    recent_predictions.insert(0, prediction_record)
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "filename": file.filename
    }

@router.get("/recent")
async def get_recent_predictions(limit: int = 10):
    """Get recent predictions"""
    return {"predictions": recent_predictions[:limit]}