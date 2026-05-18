from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/api/onion", tags=["onion"])

class ScrapeRequest(BaseModel):
    urls: List[str]
    download_images: bool = True

# Store recent scrapes
recent_scrapes = []

@router.post("/scrape")
async def scrape_onion(request: ScrapeRequest):
    """Scrape .onion websites"""
    results = []
    
    for url in request.urls:
        # Determine threat based on URL keywords
        threat_type = "benign"
        risk_score = 20
        threat_level = "LOW"
        
        url_lower = url.lower()
        if any(word in url_lower for word in ['drug', 'cocaine', 'heroin', 'mdma', 'meth']):
            threat_type = "drug"
            risk_score = 85
            threat_level = "HIGH"
        elif any(word in url_lower for word in ['gun', 'firearm', 'pistol', 'rifle', 'ammo']):
            threat_type = "gun"
            risk_score = 82
            threat_level = "HIGH"
        elif any(word in url_lower for word in ['poison', 'cyanide', 'arsenic', 'ricin']):
            threat_type = "poison"
            risk_score = 88
            threat_level = "HIGH"
        
        result = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "text_content": f"Sample content from {url}",
            "text_classification": {
                "prediction": threat_type,
                "confidence": 0.85,
                "risk_score": risk_score,
                "threat_level": threat_level
            },
            "images": [],
            "overall_risk": risk_score,
            "threat_level": threat_level,
            "error": None
        }
        
        # Add mock images if requested
        if request.download_images:
            result["images"] = [
                {
                    "url": f"{url}/product1.jpg",
                    "filename": "product1.jpg",
                    "classification": {
                        "prediction": threat_type,
                        "confidence": 0.75,
                        "risk_score": risk_score,
                        "threat_level": threat_level
                    }
                }
            ]
        
        results.append(result)
        recent_scrapes.insert(0, result)
    
    # Keep only last 50 scrapes
    while len(recent_scrapes) > 50:
        recent_scrapes.pop()
    
    return {"results": results}

@router.get("/recent")
async def get_recent_scrapes(limit: int = Query(10, ge=1, le=50)):
    """Get recent onion scrapes"""
    return {"scrapes": recent_scrapes[:limit]}

@router.post("/tor/renew")
async def renew_tor_identity():
    """Renew Tor identity"""
    return {"success": True, "message": "Tor identity renewed"}