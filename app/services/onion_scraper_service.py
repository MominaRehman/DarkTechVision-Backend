import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
import os
import re
import logging
from datetime import datetime
from PIL import Image
import torchvision.transforms as transforms
from ..config import Config
from ..models.database import db
from ..models.ml_models import model_manager
from .tor_service import tor_service

logger = logging.getLogger(__name__)

class OnionScraperService:
    def __init__(self):
        self.onion_pattern = re.compile(r'[a-z2-7]{16}\.onion')
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.bitcoin_pattern = re.compile(r'[13][a-km-zA-HJ-NP-Z0-9]{26,33}')
        self.session = None
        self.image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    async def initialize(self):
        connector = ProxyConnector.from_url(f'socks5://localhost:{Config.TOR_SOCKS_PORT}')
        self.session = aiohttp.ClientSession(connector=connector)
        
    async def classify_text(self, text):
        pred_idx, confidence = model_manager.predict_text(text)
        if pred_idx is None:
            return None
        label = Config.TEXT_CLASSES.get(pred_idx, 'unknown')
        risk_score = confidence * 100
        threat_level = 'LOW'
        if risk_score >= Config.HIGH_RISK_THRESHOLD:
            threat_level = 'HIGH'
        elif risk_score >= Config.MEDIUM_RISK_THRESHOLD:
            threat_level = 'MEDIUM'
        return {'prediction': label, 'confidence': confidence, 'risk_score': risk_score, 'threat_level': threat_level}
    
    async def classify_image(self, image_path):
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.image_transform(image).unsqueeze(0).to(model_manager.device)
            pred_idx, confidence = model_manager.predict_image(image_tensor)
            if pred_idx is None:
                return None
            label = Config.IMAGE_CLASSES.get(pred_idx, 'unknown')
            risk_score = confidence * 100
            if label in ['firearms', 'poison']:
                risk_score = min(100, risk_score * 1.2)
            threat_level = 'HIGH' if risk_score >= 70 else 'MEDIUM' if risk_score >= 40 else 'LOW'
            return {'prediction': label, 'confidence': confidence, 'risk_score': risk_score, 'threat_level': threat_level}
        except Exception as e:
            logger.error(f"Image classification error: {e}")
            return None
    
    async def scrape_onion(self, onion_url, download_images=True):
        if not onion_url.endswith('.onion'):
            onion_url = f"http://{onion_url}"
        
        result = {
            'url': onion_url,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'text_content': '',
            'images': [],
            'text_classification': None,
            'overall_risk': 0,
            'threat_level': 'LOW',
            'emails': [],
            'bitcoin_addresses': [],
            'error': None
        }
        
        try:
            async with self.session.get(onion_url, timeout=Config.ONION_TIMEOUT) as response:
                if response.status == 200:
                    html = await response.text()
                    result['success'] = True
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text_content = ' '.join(chunk for chunk in chunks if chunk)
                    result['text_content'] = text_content[:10000]
                    
                    if result['text_content']:
                        result['text_classification'] = await self.classify_text(result['text_content'])
                        result['overall_risk'] = result['text_classification'].get('risk_score', 0)
                        result['threat_level'] = result['text_classification'].get('threat_level', 'LOW')
                    
                    if download_images:
                        images = soup.find_all('img')
                        for img in images[:10]:
                            img_url = img.get('src')
                            if img_url:
                                full_url = urljoin(onion_url, img_url)
                                try:
                                    async with self.session.get(full_url, timeout=10) as img_response:
                                        if img_response.status == 200:
                                            img_data = await img_response.read()
                                            if len(img_data) <= Config.ONION_MAX_IMAGE_SIZE:
                                                img_hash = hashlib.md5(img_data).hexdigest()[:16]
                                                ext = os.path.splitext(img_url)[1] or '.jpg'
                                                filename = f"{img_hash}{ext}"
                                                onion_dir = onion_url.replace('http://', '').replace('https://', '').replace('/', '_')
                                                save_dir = os.path.join('uploads', 'onion_images', onion_dir)
                                                os.makedirs(save_dir, exist_ok=True)
                                                filepath = os.path.join(save_dir, filename)
                                                with open(filepath, 'wb') as f:
                                                    f.write(img_data)
                                                img_class = await self.classify_image(filepath)
                                                result['images'].append({
                                                    'url': full_url,
                                                    'filename': filename,
                                                    'path': filepath,
                                                    'classification': img_class
                                                })
                                                if img_class and img_class.get('risk_score', 0) > result['overall_risk']:
                                                    result['overall_risk'] = img_class['risk_score']
                                                    result['threat_level'] = img_class['threat_level']
                                except Exception as e:
                                    logger.error(f"Image download error: {e}")
                    
                    result['emails'] = list(set(self.email_pattern.findall(html)))
                    result['bitcoin_addresses'] = list(set(self.bitcoin_pattern.findall(html)))
                    
                    db.insert_onion_scrape({
                        'url': result['url'],
                        'timestamp': result['timestamp'],
                        'text_classification': result['text_classification'],
                        'images': result['images'],
                        'overall_risk': result['overall_risk'],
                        'threat_level': result['threat_level']
                    })
                    
        except asyncio.TimeoutError:
            result['error'] = f"Timeout after {Config.ONION_TIMEOUT}s"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    async def scrape_multiple(self, urls, download_images=True):
        tasks = [self.scrape_onion(url, download_images) for url in urls]
        return await asyncio.gather(*tasks)
    
    async def close(self):
        if self.session:
            await self.session.close()

onion_scraper = OnionScraperService()