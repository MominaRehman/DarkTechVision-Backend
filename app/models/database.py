from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json
from ..config import Config

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        
    def insert_document(self, collection, document):
        document["created_at"] = datetime.utcnow()
        result = self.db[collection].insert_one(document)
        return str(result.inserted_id)
    
    def find_documents(self, collection, query={}):
        return list(self.db[collection].find(query))
    
    def find_one(self, collection, query):
        return self.db[collection].find_one(query)
    
    def insert_training_log(self, epoch, loss, accuracy, model_type):
        log = {
            "epoch": epoch,
            "loss": loss,
            "accuracy": accuracy,
            "model_type": model_type,
            "timestamp": datetime.utcnow()
        }
        return self.insert_document("training_logs", log)
    
    def insert_prediction(self, input_type, input_data, prediction, confidence, risk_score):
        doc = {
            "input_type": input_type,
            "input_data": input_data,
            "prediction": prediction,
            "confidence": confidence,
            "risk_score": risk_score,
            "timestamp": datetime.utcnow()
        }
        return self.insert_document("predictions", doc)
    
    def insert_onion_scrape(self, scrape_data):
        return self.insert_document("onion_scrapes", scrape_data)

db = Database()