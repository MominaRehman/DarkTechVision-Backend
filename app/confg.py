import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "cyber_threat_intel")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Upload directories
    UPLOAD_DIR = "uploads"
    TEXT_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "text")
    IMAGE_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "images")
    ONION_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "onion")
    
    # Model paths
    TEXT_MODEL_PATH = "models/text_gcn_model.pth"
    IMAGE_MODEL_PATH = "models/vit_image_model.pth"
    
    # Training parameters
    TEXT_EPOCHS = 50
    IMAGE_EPOCHS = 10
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    
    # Threat categories
    TEXT_CLASSES = {0: 'gun', 1: 'drug', 2: 'poison'}
    IMAGE_CLASSES = {0: 'drugs', 1: 'firearms', 2: 'poison'}
    
    # Tor Configuration
    TOR_SOCKS_PORT = int(os.getenv("TOR_SOCKS_PORT", "9050"))
    TOR_CONTROL_PORT = int(os.getenv("TOR_CONTROL_PORT", "9051"))
    TOR_DATA_DIR = os.getenv("TOR_DATA_DIR", "tor/data")
    
    # Onion Scraper Settings
    ONION_TIMEOUT = int(os.getenv("ONION_TIMEOUT", "30"))
    ONION_CONCURRENT_REQUESTS = int(os.getenv("ONION_CONCURRENT_REQUESTS", "5"))
    ONION_DOWNLOAD_IMAGES = os.getenv("ONION_DOWNLOAD_IMAGES", "True").lower() == "true"
    ONION_MAX_IMAGE_SIZE = int(os.getenv("ONION_MAX_IMAGE_SIZE", "10485760"))
    
    # Threat thresholds
    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40
    LOW_RISK_THRESHOLD = 10